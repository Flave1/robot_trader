import requests
import time
import logging
from typing import Optional, Dict, Any
import os

class TradeExecutionAgent:
    """
    Trade Execution Agent (TA).
    Handles sending trade orders, setting SL/TP, monitoring fills, retrying on failure, and logging.
    Currently supports OANDA REST API.
    """
    def __init__(self, oanda_token: str, account_id: str, oanda_url: str = None):
        self.oanda_token = oanda_token
        self.account_id = account_id
        self.oanda_url = oanda_url or os.getenv("OANDA_API_URL", "https://api-fxpractice.oanda.com/v3")
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {self.oanda_token}', 'Content-Type': 'application/json'})
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('TradeExecutionAgent')

    def place_order(self, symbol: str, units: float, order_type: str = 'MARKET', sl: Optional[float] = None, tp: Optional[float] = None, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a trade order (market or limit) with SL/TP.
        """
        order = {
            "order": {
                "instrument": symbol,
                "units": str(int(units)),
                "type": order_type,
                "positionFill": "DEFAULT"
            }
        }
        if order_type == 'LIMIT' and price is not None:
            order["order"]["price"] = str(price)
        if sl:
            order["order"]["stopLossOnFill"] = {"price": str(sl)}
        if tp:
            order["order"]["takeProfitOnFill"] = {"price": str(tp)}
        url = f"{self.oanda_url}/accounts/{self.account_id}/orders"
        try:
            resp = self.session.post(url, json=order)
            resp.raise_for_status()
            data = resp.json()
            self.log_trade('Order Placed', data)
            return data
        except Exception as e:
            self.log_trade('Order Placement Failed', str(e))
            return {"error": str(e)}

    def monitor_order(self, order_id: str, max_wait: int = 30) -> bool:
        """
        Monitor order fill status. Returns True if filled, False otherwise.
        """
        url = f"{self.oanda_url}/accounts/{self.account_id}/orders/{order_id}"
        for _ in range(max_wait):
            try:
                resp = self.session.get(url)
                resp.raise_for_status()
                data = resp.json()
                state = data.get('order', {}).get('state', '')
                if state == 'FILLED':
                    self.log_trade('Order Filled', data)
                    return True
                elif state in ['CANCELLED', 'REJECTED']:  # Not filled
                    self.log_trade('Order Not Filled', data)
                    return False
            except Exception as e:
                self.log_trade('Order Monitor Error', str(e))
            time.sleep(1)
        self.log_trade('Order Fill Timeout', {'order_id': order_id})
        return False

    def retry_order(self, symbol: str, units: float, order_type: str, sl: Optional[float], tp: Optional[float], price: Optional[float], retries: int = 3) -> Dict[str, Any]:
        """
        Retry order placement up to N times if not filled.
        """
        for attempt in range(retries):
            result = self.place_order(symbol, units, order_type, sl, tp, price)
            order_id = result.get('orderCreateTransaction', {}).get('id')
            if order_id and self.monitor_order(order_id):
                return result
            self.logger.warning(f"Retrying order ({attempt+1}/{retries})...")
            time.sleep(2)
        self.logger.error("Order failed after retries.")
        return {"error": "Order failed after retries."}

    def get_spread(self, symbol: str) -> Optional[float]:
        """
        Fetch current spread for a symbol from OANDA.
        """
        url = f"{self.oanda_url}/accounts/{self.account_id}/pricing?instruments={symbol}"
        try:
            resp = self.session.get(url)
            resp.raise_for_status()
            data = resp.json()
            prices = data['prices'][0]
            spread = float(prices['asks'][0]['price']) - float(prices['bids'][0]['price'])
            return spread
        except Exception as e:
            self.log_trade('Spread Fetch Error', str(e))
            return None

    def log_trade(self, action: str, data: Any):
        """
        Log trade actions and errors.
        """
        self.logger.info(f"{action}: {data}")

    def run_trade(self, symbol: str, units: float, order_type: str = 'MARKET', sl: Optional[float] = None, tp: Optional[float] = None, price: Optional[float] = None, retries: int = 3) -> Dict[str, Any]:
        """
        Main entry: Place order with retry logic and logging.
        """
        return self.retry_order(symbol, units, order_type, sl, tp, price, retries)
