from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Trade:
    symbol: str
    type: str
    volume: float
    open_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: Optional[str] = None
    client_id: Optional[str] = None
    expiration: Optional[datetime] = None