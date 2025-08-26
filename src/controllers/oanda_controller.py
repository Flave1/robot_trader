from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService
from src.users.trader_account_service import TraderAccountService

router = APIRouter(tags=["Oanda"])

@router.get("/oanda/active-trades")
async def get_active_trades(trader_account_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """Fetch all active trades from Oanda for a specific trader account."""
    api_token, oanda_account_id, oanda_api_url, account_type = await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
    if not api_token or not oanda_account_id:
        raise HTTPException(status_code=400, detail="Oanda credentials not found for this account.")
    service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
    try:
        positions = service.get_active_positions()
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/oanda/trade")
async def execute_trade(
    trader_account_id: int = Query(...),
    symbol: str = Query(...),
    units: float = Query(...),
    take_profit: float = Query(None),
    stop_loss: float = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Execute a trade on Oanda for a specific trader account."""
    api_token, oanda_account_id, oanda_api_url, account_type = await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
    if not api_token or not oanda_account_id:
        raise HTTPException(status_code=400, detail="Oanda credentials not found for this account.")
    service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
    try:
        result = service.place_trade(symbol, units, take_profit, stop_loss)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 