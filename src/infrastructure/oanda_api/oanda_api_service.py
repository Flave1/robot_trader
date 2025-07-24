import oandapyV20
import os
from oandapyV20.endpoints.accounts import AccountDetails, AccountList
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.positions import OpenPositions
from oandapyV20.endpoints.pricing import PricingStream 
from typing import Dict, Any, List

class OandaApiService:
    def __init__(self, api_token: str = None, account_id: str = None, oanda_api_url: str = None, account_type: str = None):
        self.api_token = api_token
        self.account_id = account_id
        self.oanda_api_url = oanda_api_url
        self.account_type = account_type
        self.client = oandapyV20.API(access_token=self.api_token, environment=self.account_type)

    def format_price(self, price, decimals=5):
        return f"{float(price):.{decimals}f}"

    def place_trade(self, symbol: str, units: float, take_profit: float = None, stop_loss: float = None) -> Dict[str, Any]:
        """
        Place a trade order
        :param symbol: The trading symbol (e.g., "EUR_USD")
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

        # Only add takeProfitOnFill if valid
        if take_profit is not None and take_profit > 0:
            order_data["order"]["takeProfitOnFill"] = {"price": self.format_price(take_profit)}
        if stop_loss is not None and stop_loss > 0:
            order_data["order"]["stopLossOnFill"] = {"price": self.format_price(stop_loss)}

        order_create = OrderCreate(self.account_id, data=order_data)
        response = self.client.request(order_create)
        return response

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions for the account
        :return: List of open positions
        """
        open_positions = OpenPositions(self.account_id)
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
        
        pricing_stream = PricingStream(accountID=self.account_id, params=params)
        
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
        request = AccountDetails(accountID=self.account_id)
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