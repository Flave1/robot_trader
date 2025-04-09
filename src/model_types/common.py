from pydantic import BaseModel
from pydantic.v1 import Field

class MarketData(BaseModel):
    symbol: str = Field(default="BTCUSD", description="currency pair")