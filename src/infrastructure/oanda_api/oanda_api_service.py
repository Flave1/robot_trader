import oandapyV20
import os
from oandapyV20.endpoints.accounts import AccountDetails, AccountList
from oandapyV20.endpoints.orders import OrderCreate, OrderList, OrderDetails, OrderCancel, OrderReplace
from oandapyV20.endpoints.positions import OpenPositions
from oandapyV20.endpoints.trades import TradesList, TradeDetails, TradeClose
from oandapyV20.endpoints.pricing import PricingStream 
from typing import Dict, Any, List, Optional

class OandaApiService:
    def __init__(self, api_token: str = None, trader_account_id: str = None, oanda_api_url: str = None, account_type: str = None):
        self.api_token = api_token
        self.trader_account_id = trader_account_id
        self.oanda_api_url = oanda_api_url
        self.account_type = account_type
        self.client = oandapyV20.API(access_token=self.api_token, environment=self.account_type)

    def format_price(self, price, decimals=5):
        return f"{float(price):.{decimals}f}"

    def list_orders(self, state: str = "PENDING", count: int = 50, instrument: str = None) -> List[Dict[str, Any]]:
        """
        List orders for the account
        :param state: Order state filter (PENDING, FILLED, CANCELLED, etc.)
        :param count: Number of orders to retrieve
        :param instrument: Filter by instrument/symbol
        :return: List of orders
        """
        params = {
            "state": state,
            "count": count
        }
        if instrument:
            params["instrument"] = instrument
            
        order_list = OrderList(self.trader_account_id, params=params)
        response = self.client.request(order_list)
        return response.get("orders", [])

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get specific order details
        :param order_id: The order ID
        :return: Order details
        """
        order_details = OrderDetails(self.trader_account_id, orderID=order_id)
        response = self.client.request(order_details)
        return response

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a specific order
        :param order_id: The order ID to cancel
        :return: Cancellation response
        """
        order_cancel = OrderCancel(self.trader_account_id, orderID=order_id)
        response = self.client.request(order_cancel)
        return response

    def replace_order(self, order_id: str, new_order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace an existing order
        :param order_id: The order ID to replace
        :param new_order_data: New order data
        :return: Replacement response
        """
        order_replace = OrderReplace(self.trader_account_id, orderID=order_id, data=new_order_data)
        response = self.client.request(order_replace)
        return response

    def create_market_order(self, symbol: str, units: float, take_profit: float = None, stop_loss: float = None) -> Dict[str, Any]:
        """
        Create a market order
        :param symbol: The trading symbol
        :param units: Positive for buy, negative for sell
        :param take_profit: Optional take profit price
        :param stop_loss: Optional stop loss price
        :return: Order response
        """
        order_data = {
            "order": {
                "type": "MARKET",
                "instrument": symbol,
                "units": str(int(round(units))),
                "timeInForce": "FOK",
                "positionFill": "DEFAULT"
            }
        }

        if take_profit is not None and take_profit > 0:
            order_data["order"]["takeProfitOnFill"] = {"price": self.format_price(take_profit)}
        if stop_loss is not None and stop_loss > 0:
            order_data["order"]["stopLossOnFill"] = {"price": self.format_price(stop_loss)}

        order_create = OrderCreate(self.trader_account_id, data=order_data)
        response = self.client.request(order_create)
        return response

    def create_limit_order(self, symbol: str, units: float, price: float, take_profit: float = None, stop_loss: float = None) -> Dict[str, Any]:
        """
        Create a limit order
        :param symbol: The trading symbol
        :param units: Positive for buy, negative for sell
        :param price: Limit price
        :param take_profit: Optional take profit price
        :param stop_loss: Optional stop loss price
        :return: Order response
        """
        order_data = {
            "order": {
                "type": "LIMIT",
                "instrument": symbol,
                "units": str(int(round(units))),
                "price": self.format_price(price),
                "timeInForce": "GTC",
                "positionFill": "DEFAULT"
            }
        }

        if take_profit is not None and take_profit > 0:
            order_data["order"]["takeProfitOnFill"] = {"price": self.format_price(take_profit)}
        if stop_loss is not None and stop_loss > 0:
            order_data["order"]["stopLossOnFill"] = {"price": self.format_price(stop_loss)}

        order_create = OrderCreate(self.trader_account_id, data=order_data)
        response = self.client.request(order_create)
        return response

    def create_stop_order(self, symbol: str, units: float, price: float, take_profit: float = None, stop_loss: float = None) -> Dict[str, Any]:
        """
        Create a stop order
        :param symbol: The trading symbol
        :param units: Positive for buy, negative for sell
        :param price: Stop price
        :param take_profit: Optional take profit price
        :param stop_loss: Optional stop loss price
        :return: Order response
        """
        order_data = {
            "order": {
                "type": "STOP",
                "instrument": symbol,
                "units": str(int(round(units))),
                "price": self.format_price(price),
                "timeInForce": "GTC",
                "positionFill": "DEFAULT"
            }
        }

        if take_profit is not None and take_profit > 0:
            order_data["order"]["takeProfitOnFill"] = {"price": self.format_price(take_profit)}
        if stop_loss is not None and stop_loss > 0:
            order_data["order"]["stopLossOnFill"] = {"price": self.format_price(stop_loss)}

        order_create = OrderCreate(self.trader_account_id, data=order_data)
        response = self.client.request(order_create)
        return response

    def list_trades(self, state: str = "OPEN", count: int = 50, instrument: str = None) -> List[Dict[str, Any]]:
        """
        List trades for the account
        :param state: Trade state filter (OPEN, CLOSED, etc.)
        :param count: Number of trades to retrieve
        :param instrument: Filter by instrument/symbol
        :return: List of trades
        """
        params = {
            "state": state,
            "count": count
        }
        if instrument:
            params["instrument"] = instrument
            
        trade_list = TradesList(self.trader_account_id, params=params)
        response = self.client.request(trade_list)
        return response.get("trades", [])

    def get_trade(self, trade_id: str) -> Dict[str, Any]:
        """
        Get specific trade details
        :param trade_id: The trade ID
        :return: Trade details
        """
        trade_details = TradeDetails(self.trader_account_id, tradeID=trade_id)
        response = self.client.request(trade_details)
        return response

    def close_trade(self, trade_id: str, units: str = "ALL") -> Dict[str, Any]:
        """
        Close a trade (partial or full)
        :param trade_id: The trade ID to close
        :param units: Number of units to close ("ALL" for full close, or specific number)
        :return: Close response
        """
        close_data = {
            "units": units
        }
        trade_close = TradeClose(self.trader_account_id, tradeID=trade_id, data=close_data)
        response = self.client.request(trade_close)
        return response

    def update_trade_orders(self, trade_id: str, stop_loss: float = None, take_profit: float = None) -> Dict[str, Any]:
        """
        Set or update stop loss and take profit for a trade
        :param trade_id: The trade ID
        :param stop_loss: New stop loss price (None to remove)
        :param take_profit: New take profit price (None to remove)
        :return: Update response
        """
        # This would typically use a different endpoint, but for now we'll use order replacement
        # In practice, you might need to use the specific trade orders endpoint
        order_data = {}
        
        if stop_loss is not None:
            order_data["stopLoss"] = {"price": self.format_price(stop_loss)}
        if take_profit is not None:
            order_data["takeProfit"] = {"price": self.format_price(take_profit)}
            
        # Note: This is a simplified implementation. The actual Oanda API might require
        # a different approach for updating trade orders
        return {"status": "not_implemented", "message": "Trade order updates require specific Oanda API endpoints"}

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions for the account
        :return: List of open positions
        """
        open_positions = OpenPositions(self.trader_account_id)
        response = self.client.request(open_positions)
        return response.get("positions", [])

    def monitor_market(self, symbols: List[str]):
        """
        Monitor real-time price updates for specified symbols
        :param symbols: List of symbols to monitor (e.g., ["EUR_USD", "GBP_USD"])
        """
        params = {
            "instruments": ",".join(symbols)
        }
        
        pricing_stream = PricingStream(accountID=self.trader_account_id, params=params)
        
        for price in self.client.request(pricing_stream):
            if price["type"] == "PRICE":
                print(f"Symbol: {price['instrument']}")
                print(f"Time: {price['time']}")
                print(f"Bid: {price['bids'][0]['price']}")
                print(f"Ask: {price['asks'][0]['price']}")
                print("-------------------")

    def get_account_details(self) -> Dict[str, Any]:
        """
        Get account details
        :return: Account details
        """
        request = AccountDetails(accountID=self.trader_account_id)
        response = self.client.request(request)
        return response

    def list_accounts(self) -> List[Dict[str, Any]]:
        """
        List all accounts associated with the API token
        :return: List of accounts
        """
        request = AccountList()
        response = self.client.request(request)
        return response.get("accounts", [])