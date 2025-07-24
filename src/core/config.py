import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = Field(..., env='DATABASE_URL')
    
    # Redis Configuration
    REDIS_URL: str = Field(..., env='REDIS_URL')
    
    # API Configuration
    API_HOST: str = Field('0.0.0.0', env='API_HOST')
    API_PORT: int = Field(8000, env='API_PORT')
    
    # Logging Configuration
    LOG_LEVEL: str = Field('INFO', env='LOG_LEVEL')
    LOG_FILE: str = Field('app_logs.log', env='LOG_FILE')
    
    # Trading Configuration
    MAX_POSITION_SIZE: float = Field(1000.0, env='MAX_POSITION_SIZE')
    RISK_PER_TRADE: float = Field(0.02, env='RISK_PER_TRADE')  # 2% risk per trade
    MAX_OPEN_TRADES: int = Field(5, env='MAX_OPEN_TRADES')
    
    class Config:
        env_file = '.env'
        case_sensitive = True

settings = Settings()

def get_settings() -> Settings:
    return settings 