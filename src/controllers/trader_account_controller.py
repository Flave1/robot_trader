from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.users.trader_account_service import TraderAccountService
from src.users.models import TraderAccountUpdate, TraderAccountResponse, TraderAccountCreate
from typing import Dict, Any, List
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService

router = APIRouter(tags=["TraderAccount"])

@router.get("/trader-accounts/{user_id}")
async def get_trader_accounts(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all trader accounts for a user (includes api_token and oanda_account_id in response)"""
    trader_accounts = await TraderAccountService.get_trader_accounts_by_user_id(db, user_id)
    return [TraderAccountResponse.from_orm(account) for account in trader_accounts]

@router.get("/trader-account/{trader_account_id}")
async def get_trader_account(trader_account_id  : int, db: AsyncSession = Depends(get_db)):
    """Get specific trader account by ID (includes api_token and oanda_account_id in response)"""
    trader_account = await TraderAccountService.get_trader_account_by_id(db, trader_account_id)
    if not trader_account:
        raise HTTPException(status_code=404, detail="Trader account not found")
    return TraderAccountResponse.from_orm(trader_account)

@router.get("/trader-account/{user_id}/default")
async def get_default_trader_account(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get the default trader account for a user (persisted in DB)"""
    trader_account = await TraderAccountService.get_default_trader_account(db, user_id)
    if not trader_account:
        raise HTTPException(status_code=404, detail="No trader account found")
    return TraderAccountResponse.from_orm(trader_account)

@router.post("/trader-account")
async def create_trader_account(
    trader_account: TraderAccountCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new trader account. Accepts api_token and oanda_account_id for Oanda integration.
    """
    try:
        new_account = await TraderAccountService.create_trader_account(db, trader_account)
        return TraderAccountResponse.from_orm(new_account)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create trader account: {str(e)}")

@router.put("/trader-account/{trader_account_id}")
async def update_trader_account(
    trader_account_id: int,
    trader_account_update: TraderAccountUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update trader account settings, including api_token and oanda_account_id.
    """
    updated_account = await TraderAccountService.update_trader_account(db, trader_account_id, trader_account_update)
    if not updated_account:
        raise HTTPException(status_code=404, detail="Trader account not found")
    return TraderAccountResponse.from_orm(updated_account)

@router.get("/trader-account/{trader_account_id}/trading-permissions")
async def check_trading_permissions(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """Check if account can trade based on settings"""
    permissions = await TraderAccountService.check_trading_permissions(db, trader_account_id)
    return permissions

@router.post("/trader-account/{trader_account_id}/deactivate")
async def deactivate_trader_account(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate a trader account"""
    deactivated_account = await TraderAccountService.deactivate_account(db, trader_account_id)
    if not deactivated_account:
        raise HTTPException(status_code=404, detail="Trader account not found")
    return {"message": "Trader account deactivated successfully"}

@router.post("/trader-account/{trader_account_id}/activate")
async def activate_trader_account(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """Activate a trader account"""
    activated_account = await TraderAccountService.activate_account(db, trader_account_id)
    if not activated_account:
        raise HTTPException(status_code=404, detail="Trader account not found")
    return {"message": "Trader account activated successfully"}

@router.get("/trader-accounts/active")
async def get_all_active_accounts(db: AsyncSession = Depends(get_db)):
    """Get all active trader accounts (admin endpoint)"""
    active_accounts = await TraderAccountService.get_all_active_accounts(db)
    return [TraderAccountResponse.from_orm(account) for account in active_accounts]

@router.get("/trader-account/{trader_account_id}/oanda")
async def get_oanda_account_details(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get live Oanda account details for the given account and update local TraderAccount.
    """
     
    try: 
        # Update local TraderAccount with latest balance and currency
        from src.users.trader_account_service import TraderAccountService
        from src.users.models import TraderAccountUpdate
        api_token, oanda_account_id, oanda_api_url, account_type = await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        if not api_token or not oanda_account_id:
            raise HTTPException(status_code=400, detail="Oanda credentials not found for this account.")
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        oanda_account = oanda_service.get_account_details()
        account_data = oanda_account.get("account", {})

       
        update_data = {}
        if "balance" in account_data:
            update_data["account_balance"] = float(account_data["balance"])
        if "currency" in account_data:
            update_data["trading_currency"] = account_data["currency"]
        # Add more fields as needed

        if update_data:
            await TraderAccountService.update_trader_account(
                db, trader_account_id, TraderAccountUpdate(**update_data)
            )

        relevant_info = {
            "trader_account_id": account_data.get("id"),
            "balance": account_data.get("balance"),
            "marginAvailable": account_data.get("marginAvailable"),
            "marginUsed": account_data.get("marginUsed"),
            "openTradeCount": account_data.get("openTradeCount"),
            "openPositionCount": account_data.get("openPositionCount"),
            "pl": account_data.get("pl"),
            "unrealizedPL": account_data.get("unrealizedPL"),
            "currency": account_data.get("currency"),
        }
        return relevant_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Oanda account details: {str(e)}")

@router.post("/trader-account/switch")
async def switch_trader_account(
    user_id: str,
    trader_account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Set the default trader account for a user (persisted in DB).
    """
    updated = await TraderAccountService.set_default_trader_account(db, user_id, trader_account_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Failed to switch trader account")
    return {"message": "Default trader account switched successfully"} 

@router.get("/trader-account/{trader_account_id}/state")
async def get_account_state(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed account state including open trades count and drawdown"""
    try:
        account_state = await TraderAccountService.get_account_state(db, trader_account_id)
        return account_state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account state: {str(e)}")

@router.get("/trader-account/{trader_account_id}/open-trades")
async def get_open_trades_details(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed information about open trades for a trader account"""
    try:
        open_trades = await TraderAccountService.get_open_trades_details(db, trader_account_id)
        return {
            "trader_account_id": trader_account_id,
            "open_trades_count": len(open_trades),
            "trades": open_trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching open trades: {str(e)}")

@router.get("/trader-account/{trader_account_id}/drawdown")
async def get_account_drawdown(trader_account_id: int, db: AsyncSession = Depends(get_db)):
    """Get current drawdown percentage for a trader account"""
    try:
        drawdown = await TraderAccountService.calculate_drawdown(db, trader_account_id)
        return {
            "trader_account_id": trader_account_id,
            "drawdown_percentage": drawdown,
            "drawdown_decimal": drawdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating drawdown: {str(e)}") 