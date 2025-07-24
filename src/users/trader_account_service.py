from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.users.models import TraderAccount, TraderAccountCreate, TraderAccountUpdate, TraderAccountsTrades, TraderAccountsTradesCreate, TraderAccountsTradesUpdate, User
from typing import Optional, List
from datetime import datetime
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService

class TraderAccountService:
    """Service for managing trader accounts"""
    
    @staticmethod
    async def create_trader_account(db: AsyncSession, trader_account: TraderAccountCreate) -> TraderAccount:
        """Create a new trader account for a user"""
        db_trader_account = TraderAccount(
            user_id=trader_account.user_id,
            account_name=trader_account.account_name,
            account_type=trader_account.account_type,
            account_balance=trader_account.account_balance,
            max_trades=trader_account.max_trades,
            risk_pct=trader_account.risk_pct,
            preferred_timeframe=trader_account.preferred_timeframe,
            trading_currency=trader_account.trading_currency,
            max_drawdown=trader_account.max_drawdown,
            daily_loss_limit=trader_account.daily_loss_limit,
            weekly_loss_limit=trader_account.weekly_loss_limit,
            api_token=trader_account.api_token,
            oanda_account_id=trader_account.oanda_account_id,
            oanda_api_url=getattr(trader_account, 'oanda_api_url', None)
        )
        
        db.add(db_trader_account)
        await db.commit()
        await db.refresh(db_trader_account)
        return db_trader_account
    
    @staticmethod
    async def get_trader_account_by_id(db: AsyncSession, account_id: int) -> Optional[TraderAccount]:
        """Get trader account by account ID"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        return result.scalars().first()
    
    @staticmethod
    async def get_trader_accounts_by_user_id(db: AsyncSession, user_id: str) -> List[TraderAccount]:
        """Get all trader accounts for a user"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.user_id == user_id))
        return result.scalars().all()
    
    @staticmethod
    async def set_default_trader_account(db: AsyncSession, user_id: str, account_id: int) -> bool:
        """Set the default trader account for a user"""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.default_trader_account_id = account_id
            await db.commit()
            await db.refresh(user)
            return True
        return False

    @staticmethod
    async def get_default_trader_account(db: AsyncSession, user_id: str) -> Optional[TraderAccount]:
        """Get the first trader account for a user (no default logic)"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.user_id == user_id).limit(1))
        return result.scalars().first()
    
    @staticmethod
    async def update_trader_account(db: AsyncSession, account_id: int, trader_account_update: TraderAccountUpdate) -> Optional[TraderAccount]:
        """Update trader account settings"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        db_trader_account = result.scalars().first()
        
        if db_trader_account:
            update_data = trader_account_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_trader_account, key, value)
            
            db_trader_account.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trader_account)
        
        return db_trader_account
    
    @staticmethod
    async def update_account_balance(db: AsyncSession, account_id: int, new_balance: float) -> Optional[TraderAccount]:
        """Update account balance (for trade execution)"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        db_trader_account = result.scalars().first()
        
        if db_trader_account:
            db_trader_account.account_balance = new_balance
            db_trader_account.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trader_account)
        
        return db_trader_account
    
    @staticmethod
    async def deactivate_account(db: AsyncSession, account_id: int) -> Optional[TraderAccount]:
        """Deactivate a trader account"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        db_trader_account = result.scalars().first()
        
        if db_trader_account:
            db_trader_account.is_active = False
            db_trader_account.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trader_account)
        
        return db_trader_account
    
    @staticmethod
    async def activate_account(db: AsyncSession, account_id: int) -> Optional[TraderAccount]:
        """Activate a trader account"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        db_trader_account = result.scalars().first()
        
        if db_trader_account:
            db_trader_account.is_active = True
            db_trader_account.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trader_account)
        
        return db_trader_account
    
    @staticmethod
    async def get_all_active_accounts(db: AsyncSession) -> List[TraderAccount]:
        """Get all active trader accounts"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.is_active == True))
        return result.scalars().all()
    
    @staticmethod
    async def check_trading_permissions(db: AsyncSession, account_id: int) -> dict:
        """Check if account can trade based on settings"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        db_trader_account = result.scalars().first()
        
        if not db_trader_account:
            return {
                "can_trade": False,
                "reason": "No trader account found"
            }
        
        if not db_trader_account.is_active:
            return {
                "can_trade": False,
                "reason": "Account is deactivated"
            }
        
        # Add more checks here as needed (e.g., drawdown limits, daily loss limits)
        
        return {
            "can_trade": True,
            "account_balance": db_trader_account.account_balance,
            "max_trades": db_trader_account.max_trades,
            "risk_pct": db_trader_account.risk_pct,
            "max_drawdown": db_trader_account.max_drawdown
        }

    @staticmethod
    async def get_account_state(db: AsyncSession, account_id: int) -> dict:
        """Get account state"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        db_trader_account = result.scalars().first()

        account_state = {
            'account_balance': db_trader_account.account_balance,
            'open_trades': 0, 
            'max_trades': 5,
            'drawdown': 0.0,
            'max_drawdown': 0.2,
            'risk_pct': db_trader_account.risk_pct
        }

        return account_state

    @staticmethod
    async def get_oanda_credentials_by_account_id(db: AsyncSession, account_id: int) -> tuple[str | None, str | None]:
        """Fetch api_token and oanda_account_id for a trader account by account_id"""
        result = await db.execute(select(TraderAccount).filter(TraderAccount.id == account_id))
        trader_account = result.scalars().first()
        if trader_account:
            return trader_account.api_token, trader_account.oanda_account_id, trader_account.oanda_api_url, trader_account.account_type
        return None, None

class TraderAccountsTradesService:
    """Service for managing trader account trades"""
    
    @staticmethod
    async def create_trade(db: AsyncSession, trade: TraderAccountsTradesCreate) -> TraderAccountsTrades:
        """Create a new trade record"""
        db_trade = TraderAccountsTrades(
            trader_account_id=trade.trader_account_id,
            symbol=trade.symbol,
            trade_type=trade.trade_type,
            units=trade.units,
            entry_price=trade.entry_price,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            oanda_order_id=trade.oanda_order_id,
            oanda_position_id=trade.oanda_position_id
        )
        
        db.add(db_trade)
        await db.commit()
        await db.refresh(db_trade)
        return db_trade
    
    @staticmethod
    async def get_trade_by_id(db: AsyncSession, trade_id: int) -> Optional[TraderAccountsTrades]:
        """Get trade by ID"""
        result = await db.execute(select(TraderAccountsTrades).filter(TraderAccountsTrades.id == trade_id))
        return result.scalars().first()
    
    @staticmethod
    async def get_trades_by_account_id(db: AsyncSession, account_id: int) -> List[TraderAccountsTrades]:
        """Get all trades for a specific account"""
        result = await db.execute(select(TraderAccountsTrades).filter(TraderAccountsTrades.trader_account_id == account_id))
        return result.scalars().all()
    
    @staticmethod
    async def get_open_trades_by_account_id(db: AsyncSession, account_id: int) -> List[TraderAccountsTrades]:
        """Get all open trades for a specific account, syncing with Oanda first if possible."""
        # Fetch Oanda credentials for the trader account
        api_token, oanda_account_id, oanda_api_url, account_type = await TraderAccountService.get_oanda_credentials_by_account_id(db, account_id)
        if not api_token or not oanda_account_id:
            return []
        try:
            oanda_service = OandaApiService(api_token=api_token, account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
            oanda_positions = oanda_service.get_active_positions()  # Synchronous call

            # Fetch open trades from DB
            result = await db.execute(select(TraderAccountsTrades).filter(
                TraderAccountsTrades.trader_account_id == account_id,
                TraderAccountsTrades.status == "open"
            ))
            db_trades = result.scalars().all()

            # Build lookup for DB trades by (symbol, trade_type)
            db_trades_by_symbol = {(t.symbol, t.trade_type): t for t in db_trades}
            oanda_symbols = set()
            for pos in oanda_positions:
                symbol = pos["instrument"]
                for side in ["long", "short"]:
                    units = float(pos[side]["units"])
                    if units == 0:
                        continue
                    trade_type = "buy" if side == "long" else "sell"
                    oanda_symbols.add((symbol, trade_type))
                    entry_price = float(pos[side]["averagePrice"])
                    oanda_order_id = pos.get("pl", None)  # Use a better unique field if available
                    unrealized_pl = float(pos[side].get("unrealizedPL", 0))
                    db_trade = db_trades_by_symbol.get((symbol, trade_type))
                    if db_trade:
                        db_trade.units = units
                        db_trade.entry_price = entry_price
                        db_trade.oanda_order_id = oanda_order_id
                        db_trade.unrealized_pl = unrealized_pl
                        db_trade.updated_at = datetime.utcnow()
                    else:
                        new_trade = TraderAccountsTrades(
                            trader_account_id=account_id,
                            symbol=symbol,
                            trade_type=trade_type,
                            units=units,
                            entry_price=entry_price,
                            status="open",
                            oanda_order_id=oanda_order_id,
                            unrealized_pl=unrealized_pl,
                            entry_time=datetime.utcnow(),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.add(new_trade)

            # Mark DB trades as closed if not in Oanda
            for db_trade in db_trades:
                if (db_trade.symbol, db_trade.trade_type) not in oanda_symbols:
                    db_trade.status = "closed"
                    db_trade.exit_time = datetime.utcnow()
                    db_trade.updated_at = datetime.utcnow()

            await db.commit()
        except Exception as e:
            print(f"Oanda sync failed for account {account_id}: {e}")

        # Return updated open trades from DB
        result = await db.execute(select(TraderAccountsTrades).filter(
            TraderAccountsTrades.trader_account_id == account_id,
            TraderAccountsTrades.status == "open"
        ))
        return result.scalars().all()
    
    @staticmethod
    async def update_trade(db: AsyncSession, trade_id: int, trade_update: TraderAccountsTradesUpdate) -> Optional[TraderAccountsTrades]:
        """Update trade information"""
        result = await db.execute(select(TraderAccountsTrades).filter(TraderAccountsTrades.id == trade_id))
        db_trade = result.scalars().first()
        
        if db_trade:
            update_data = trade_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_trade, key, value)
            
            db_trade.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trade)
        
        return db_trade
    
    @staticmethod
    async def close_trade(db: AsyncSession, trade_id: int, exit_price: float, realized_pl: float) -> Optional[TraderAccountsTrades]:
        """Close a trade with exit price and realized P&L"""
        result = await db.execute(select(TraderAccountsTrades).filter(TraderAccountsTrades.id == trade_id))
        db_trade = result.scalars().first()
        
        if db_trade:
            db_trade.status = "closed"
            db_trade.exit_price = exit_price
            db_trade.exit_time = datetime.utcnow()
            db_trade.realized_pl = realized_pl
            db_trade.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trade)
        
        return db_trade
    
    @staticmethod
    async def cancel_trade(db: AsyncSession, trade_id: int) -> Optional[TraderAccountsTrades]:
        """Cancel a trade"""
        result = await db.execute(select(TraderAccountsTrades).filter(TraderAccountsTrades.id == trade_id))
        db_trade = result.scalars().first()
        
        if db_trade:
            db_trade.status = "cancelled"
            db_trade.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trade)
        
        return db_trade
    
    @staticmethod
    async def update_unrealized_pl(db: AsyncSession, trade_id: int, unrealized_pl: float) -> Optional[TraderAccountsTrades]:
        """Update unrealized P&L for an open trade"""
        result = await db.execute(select(TraderAccountsTrades).filter(TraderAccountsTrades.id == trade_id))
        db_trade = result.scalars().first()
        
        if db_trade:
            db_trade.unrealized_pl = unrealized_pl
            db_trade.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_trade)
        
        return db_trade 