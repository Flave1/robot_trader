-- Migration: Add default_trader_account_id column to users table
-- This migration adds the missing column that's referenced in the SQLAlchemy model

-- Add the default_trader_account_id column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS default_trader_account_id INTEGER;

-- Add a comment to document the column
COMMENT ON COLUMN users.default_trader_account_id IS 'Foreign key reference to trader_accounts.id for the user''s default trading account';

-- Create an index for better performance on lookups
CREATE INDEX IF NOT EXISTS idx_users_default_trader_account_id ON users(default_trader_account_id);