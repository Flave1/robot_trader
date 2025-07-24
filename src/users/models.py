from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from pydantic import BaseModel, EmailStr, RootModel
from typing import Optional, Dict, Any
from src.database import Base # Ensure Base is imported from src.database
from datetime import datetime
# from typing import Optional
# import email_validator # Removed explicit import

# Assuming Base is imported from database.py if it's moved there
# For now, let's define it here for clarity
# Base = declarative_base()
# class Base(AsyncAttrs, DeclarativeBase):
#     pass

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    # Personal Identification Information (KYC)
    full_legal_name = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)

    # Residential Information
    residential_address = Column(String, nullable=True)
    proof_of_address_url = Column(String, nullable=True)

    # Identity Verification Documents
    government_id_url = Column(String, nullable=True)

    # Financial Information
    employment_status = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    annual_income = Column(Integer, nullable=True)
    source_of_funds = Column(String, nullable=True)
    net_worth = Column(Integer, nullable=True)
    bank_account_details = Column(String, nullable=True)

    # Trading Experience and Knowledge (Suitability Assessment)
    trading_experience = Column(String, nullable=True)
    knowledge_assessment_score = Column(Integer, nullable=True)
    risk_tolerance = Column(String, nullable=True)

    # Account and Security Information
    account_type = Column(String, nullable=True)
    trading_currency = Column(String, nullable=True)
    tax_identification_number = Column(String, nullable=True)

    # Regulatory Disclosures and Agreements
    agreed_terms = Column(Boolean, default=False, nullable=True)
    agreed_risk_disclosure = Column(Boolean, default=False, nullable=True)
    agreed_privacy_policy = Column(Boolean, default=False, nullable=True)
    agreed_aml_kyc_policy = Column(Boolean, default=False, nullable=True)

    # Relationship - Updated to support multiple accounts
    trader_accounts = relationship("TraderAccount", back_populates="user")
    default_trader_account_id = Column(Integer, nullable=True)


class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    google_user_id: Optional[str] = None

    @property
    def is_google_auth(self) -> bool:
        return bool(self.google_user_id and not self.password)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_legal_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    phone_number: Optional[str] = None
    residential_address: Optional[str] = None
    proof_of_address_url: Optional[str] = None
    government_id_url: Optional[str] = None
    employment_status: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[int] = None
    source_of_funds: Optional[str] = None
    net_worth: Optional[int] = None
    bank_account_details: Optional[str] = None
    trading_experience: Optional[str] = None
    knowledge_assessment_score: Optional[int] = None
    risk_tolerance: Optional[str] = None
    account_type: Optional[str] = None
    trading_currency: Optional[str] = None
    tax_identification_number: Optional[str] = None
    agreed_terms: Optional[bool] = None
    agreed_risk_disclosure: Optional[bool] = None
    agreed_privacy_policy: Optional[bool] = None
    agreed_aml_kyc_policy: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_legal_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    phone_number: Optional[str] = None
    residential_address: Optional[str] = None
    proof_of_address_url: Optional[str] = None
    government_id_url: Optional[str] = None
    employment_status: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[int] = None
    source_of_funds: Optional[str] = None
    net_worth: Optional[int] = None
    bank_account_details: Optional[str] = None
    trading_experience: Optional[str] = None
    knowledge_assessment_score: Optional[int] = None
    risk_tolerance: Optional[str] = None
    account_type: Optional[str] = None
    trading_currency: Optional[str] = None
    tax_identification_number: Optional[str] = None
    agreed_terms: Optional[bool] = None
    agreed_risk_disclosure: Optional[bool] = None
    agreed_privacy_policy: Optional[bool] = None
    agreed_aml_kyc_policy: Optional[bool] = None

    class Config:
        from_attributes = True

# Dynamic Pydantic model for sectionalized user profile response
class SectionalizedProfileResponse(RootModel):
    root: Dict[str, Dict[str, Any]]

class ProfileCompletionResponse(BaseModel):
    percentage_completion: float

class TraderAccount(Base):
    __tablename__ = "trader_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account_name = Column(String, nullable=False)  # User-defined account name
    account_type = Column(String, nullable=False, default="demo")  # "demo" or "real"
    
    # Account Balance and Risk Management
    account_balance = Column(Float, default=10000.0, nullable=False)  # Default $10,000
    max_trades = Column(Integer, default=5, nullable=False)  # Maximum concurrent trades
    risk_pct = Column(Float, default=0.02, nullable=False)  # Default 2% risk per trade
    
    # Trading Preferences
    preferred_timeframe = Column(String, default="M15", nullable=False)
    trading_currency = Column(String, default="USD", nullable=False)
    
    # Risk Management Settings
    max_drawdown = Column(Float, default=0.20, nullable=False)  # Maximum 20% drawdown
    daily_loss_limit = Column(Float, default=0.05, nullable=False)  # 5% daily loss limit
    weekly_loss_limit = Column(Float, default=0.15, nullable=False)  # 15% weekly loss limit
    
    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="trader_accounts")
    trades = relationship("TraderAccountsTrades", back_populates="trader_account")
    api_token = Column(String, nullable=True)
    oanda_account_id = Column(String, nullable=True)
    oanda_api_url = Column(String, nullable=True)  # Added field


class TraderAccountsTrades(Base):
    __tablename__ = "trader_accounts_trades"

    id = Column(Integer, primary_key=True, index=True)
    trader_account_id = Column(Integer, ForeignKey("trader_accounts.id"), nullable=False)
    
    # Trade Information
    symbol = Column(String, nullable=False)
    trade_type = Column(String, nullable=False)  # "buy" or "sell"
    units = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Trade Status
    status = Column(String, nullable=False, default="open")  # "open", "closed", "cancelled"
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    
    # P&L Information
    realized_pl = Column(Float, nullable=True)
    unrealized_pl = Column(Float, nullable=True)
    
    # Trade Metadata
    oanda_order_id = Column(String, nullable=True)  # Oanda order ID for reference
    oanda_position_id = Column(String, nullable=True)  # Oanda position ID for reference
    
    # Timestamps
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    trader_account = relationship("TraderAccount", back_populates="trades")


# Update relationship in User model
User.trader_accounts = relationship("TraderAccount", back_populates="user")

class TraderAccountCreate(BaseModel):
    user_id: str
    account_name: str
    account_type: str = "demo"
    account_balance: Optional[float] = 10000.0
    max_trades: Optional[int] = 5
    risk_pct: Optional[float] = 0.02
    preferred_timeframe: Optional[str] = "M15"
    trading_currency: Optional[str] = "USD"
    max_drawdown: Optional[float] = 0.20
    daily_loss_limit: Optional[float] = 0.05
    weekly_loss_limit: Optional[float] = 0.15
    api_token: Optional[str] = None
    oanda_account_id: Optional[str] = None
    oanda_api_url: Optional[str] = None  # Added field

class TraderAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    account_balance: Optional[float] = None
    max_trades: Optional[int] = None
    risk_pct: Optional[float] = None
    preferred_timeframe: Optional[str] = None
    trading_currency: Optional[str] = None
    max_drawdown: Optional[float] = None
    daily_loss_limit: Optional[float] = None
    weekly_loss_limit: Optional[float] = None
    is_active: Optional[bool] = None
    api_token: Optional[str] = None
    oanda_account_id: Optional[str] = None
    oanda_api_url: Optional[str] = None  # Added field

class TraderAccountResponse(BaseModel):
    id: int
    user_id: str
    account_name: str
    account_type: str
    account_balance: float
    max_trades: int
    risk_pct: float
    preferred_timeframe: str
    trading_currency: str
    max_drawdown: float
    daily_loss_limit: float
    weekly_loss_limit: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    api_token: Optional[str] = None
    oanda_account_id: Optional[str] = None
    oanda_api_url: Optional[str] = None  # Added field

    class Config:
        from_attributes = True


class TraderAccountsTradesCreate(BaseModel):
    trader_account_id: int
    symbol: str
    trade_type: str
    units: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    oanda_order_id: Optional[str] = None
    oanda_position_id: Optional[str] = None

class TraderAccountsTradesUpdate(BaseModel):
    status: Optional[str] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    realized_pl: Optional[float] = None
    unrealized_pl: Optional[float] = None

class TraderAccountsTradesResponse(BaseModel):
    id: int
    trader_account_id: int
    symbol: str
    trade_type: str
    units: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    realized_pl: Optional[float] = None
    unrealized_pl: Optional[float] = None
    oanda_order_id: Optional[str] = None
    oanda_position_id: Optional[str] = None
    entry_time: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 