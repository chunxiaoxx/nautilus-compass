-- Add Google OAuth support to users table
-- Migration: add_google_oauth
-- Date: 2026-03-02

-- Add google_id column
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);

-- Add unique constraint
ALTER TABLE users ADD CONSTRAINT users_google_id_unique UNIQUE (google_id);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Add comment
COMMENT ON COLUMN users.google_id IS 'Google OAuth user ID';
