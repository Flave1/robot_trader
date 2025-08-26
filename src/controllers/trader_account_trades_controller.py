from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.users.trader_account_service import TraderAccountsTradesService, TraderAccountService
from src.users.models import (
    TraderAccountsTradesCreate, 
    TraderAccountsTradesUpdate, 
    TraderAccountsTradesResponse
)
from typing import List

router = APIRouter(tags=["TraderAccountTrades"])

@router.post("/trader-account-trades")
async def create_trade(
    trade: TraderAccountsTradesCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create a new trade record"""
    try:
        new_trade = await TraderAccountsTradesService.create_trade(db, trade)
        return TraderAccountsTradesResponse.from_orm(new_trade)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create trade: {str(e)}")

@router.get("/trader-account-trades/{trade_id}")
async def get_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific trade by ID"""
    trade = await TraderAccountsTradesService.get_trade_by_id(db, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TraderAccountsTradesResponse.from_orm(trade)

@router.get("/trader-account-trades/account/{trader_account_id}")
async def get_trades_by_account(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """Get all trades for a specific account"""
    trades = await TraderAccountsTradesService.get_trades_by_account_id(db, trader_account_id)
    return [TraderAccountsTradesResponse.from_orm(trade) for trade in trades]

@router.get("/trader-account-trades/account/{trader_account_id}/open/{user_id}")
async def get_open_trades_by_account(trader_account_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all open trades for a specific account, or for the user's default account if trader_account_id is 'default' and user_id is provided"""
    if trader_account_id == 'default' and user_id:
        default_account = await TraderAccountService.get_default_trader_account(db, user_id)
        if not default_account:
            raise HTTPException(status_code=404, detail="No default trader account found")
        trader_account_id = default_account.id
    else:
        trader_account_id = int(trader_account_id)
    trades = await TraderAccountsTradesService.get_open_trades_by_account_id(db, trader_account_id)
    return [TraderAccountsTradesResponse.from_orm(trade) for trade in trades]

@router.put("/trader-account-trades/{trade_id}")
async def update_trade(
    trade_id: int, 
    trade_update: TraderAccountsTradesUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update trade information"""
    updated_trade = await TraderAccountsTradesService.update_trade(db, trade_id, trade_update)
    if not updated_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TraderAccountsTradesResponse.from_orm(updated_trade)

@router.post("/trader-account-trades/{trade_id}/close")
async def close_trade(
    trade_id: int, 
    exit_price: float, 
    realized_pl: float, 
    db: AsyncSession = Depends(get_db)
):
    """Close a trade with exit price and realized P&L"""
    closed_trade = await TraderAccountsTradesService.close_trade(db, trade_id, exit_price, realized_pl)
    if not closed_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TraderAccountsTradesResponse.from_orm(closed_trade)

@router.post("/trader-account-trades/{trade_id}/cancel")
async def cancel_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a trade"""
    cancelled_trade = await TraderAccountsTradesService.cancel_trade(db, trade_id)
    if not cancelled_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TraderAccountsTradesResponse.from_orm(cancelled_trade)

@router.put("/trader-account-trades/{trade_id}/unrealized-pl")
async def update_unrealized_pl(
    trade_id: int, 
    unrealized_pl: float, 
    db: AsyncSession = Depends(get_db)
):
    """Update unrealized P&L for an open trade"""
    updated_trade = await TraderAccountsTradesService.update_unrealized_pl(db, trade_id, unrealized_pl)
    if not updated_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TraderAccountsTradesResponse.from_orm(updated_trade) 