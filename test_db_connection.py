#!/usr/bin/env python3
"""
Test database connection
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    """Test the database connection"""
    try:
        # Test with asyncpg directly
        conn = await asyncpg.connect(
            user="arbix_user",
            password="arbix_password!1",
            database="arbix_db",
            host="localhost",
            port=5434
        )
        
        # Test a simple query
        result = await conn.fetchval("SELECT version()")
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {result}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection()) 