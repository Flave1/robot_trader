from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Construct DATABASE_URL from environment variables, defaulting to 'db' for Docker Compose
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://arbix_user:arbix_password!1@db:5432/arbix_db")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close() 