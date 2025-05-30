from src.application.services.oanda_trading_app_service import OandaTradingAppService

def place_trade(symbol: str, units: float, take_profit: float = None, stop_loss: float = None):
    trading_service = OandaTradingAppService()
    return trading_service.place_trade(
        symbol=symbol,
        units=units,
        take_profit=take_profit,
        stop_loss=stop_loss
    )

def get_active_positions():
    trading_service = OandaTradingAppService()
    return trading_service.get_active_positions()