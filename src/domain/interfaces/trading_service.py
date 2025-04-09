from abc import ABC, abstractmethod
from ..entities.trade import Trade

class TradingService(ABC):
    @abstractmethod
    async def execute_trade(self, trade: Trade):
        pass

    @abstractmethod
    async def get_market_data(self, symbol: str):
        pass

    @abstractmethod
    async def get_positions(self):
        pass

    @abstractmethod
    async def monitor_position(self, position_id: str):
        pass