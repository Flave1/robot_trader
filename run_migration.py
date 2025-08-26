#!/usr/bin/env python3
"""
Database migration script to add the missing default_trader_account_id column.
Run this script to fix the database schema issue.
"""

import asyncio
import os
from sqlalchemy import text
from src.database import engine

async def run_migration():
    """Run the migration to add default_trader_account_id column"""
    print("Starting database migration...")
    
    async with engine.begin() as conn:
        try:
            # Add the default_trader_account_id column
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS default_trader_account_id INTEGER;
            """))
            
            # Add a comment to document the column
            await conn.execute(text("""
                COMMENT ON COLUMN users.default_trader_account_id IS 'Foreign key reference to trader_accounts.id for the user''s default trading account';
            """))
            
            # Create an index for better performance on lookups
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_default_trader_account_id ON users(default_trader_account_id);
            """))
            
            print("✅ Migration completed successfully!")
            print("✅ Added default_trader_account_id column to users table")
            print("✅ Added index for better performance")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(run_migration())