from typing import Dict, Any, List
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService

class OandaTradingAppService:
    def __init__(self):
        self.oanda_service = OandaApiService()

    def place_trade(self, symbol: str, units: float, take_profit: float = None, stop_loss: float = None) -> Dict[str, Any]:
        """
        Place a trade using the OANDA API
        """
        try:
            response = self.oanda_service.place_trade(symbol, units, take_profit, stop_loss)
            return {
                "success": True,
                "order": response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_active_positions(self) -> Dict[str, Any]:
        """
        Get all active positions
        """
        try:
            positions = self.oanda_service.get_active_positions()
            return {
                "success": True,
                "positions": positions
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def monitor_market(self, symbols: List[str]) -> None:
        """
        Monitor real-time market data for specified symbols
        """
        try:
            self.oanda_service.monitor_market(symbols)
        except Exception as e:
            print(f"Error monitoring market: {str(e)}")