from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Default credentials for trade execution when the user does not provide credentials.
    These values are loaded from the environment file (.env) to ensure security and flexibility.
    """
    login_id: str = Field(..., env="ACCOUNT_LOGIN", description="Default login ID used for trading if the user does not provide one.")
    password: str = Field(..., env="BROKER_PASSWORD", description="Default password for authentication when user credentials are missing.")
    broker_name: str = Field(..., env="BROKER_SERVER_NAME", description="Default broker name used when no broker is specified.")
    
    # Add the additional fields that were causing validation errors
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    tavily_api_key: str | None = None
    groq_api_key: str | None = None
    meta_api_token: str | None = None
    langsmith_api_key: str | None = None
    langchain_callbacks_background: bool = False
    langchain_tracing_v2: bool = False

    class Config:
        env_file = ".env"  # Loads values from .env file
        extra = "allow"  # Allow extra fields in the settings

# Initialize settings
settings = Settings()
