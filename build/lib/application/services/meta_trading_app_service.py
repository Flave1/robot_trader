from ...domain.entities.trade import Trade
from ...domain.interfaces.trading_service import TradingService
from datetime import datetime, timedelta

class MetaTradingAppService:
    def __init__(self, trading_service: TradingService):
        self.trading_service = trading_service

    async def place_trade(self, symbol: str, trade_type: str, volume: float, price: float, 
                         stop_loss: float = None, take_profit: float = None):
        trade = Trade(
            symbol=symbol,
            type=trade_type,
            volume=volume,
            open_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            client_id=f"TE_{symbol}_{datetime.now().timestamp()}",
            expiration=datetime.now() + timedelta(days=1)
        )
        return await self.trading_service.execute_trade(trade)

    async def monitor_market(self, symbol: str):
        return await self.trading_service.get_market_data(symbol)

    async def get_active_positions(self):
        return await self.trading_service.get_positions()

    async def monitor_specific_position(self, position_id: str):
        return await self.trading_service.monitor_position(position_id)