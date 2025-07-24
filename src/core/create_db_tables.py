from src.database import Base, engine
from src.users import models as user_models
import asyncio

async def create_tables():
    print(f"Using DATABASE_URL: {engine.url}")
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables()) 