"""
Database migration: Add OAuth fields to users table

Run this script to add GitHub and Google OAuth fields to the users table.
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    """Add OAuth fields to users table."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Add GitHub OAuth fields
        try:
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS github_id VARCHAR(50) UNIQUE,
                ADD COLUMN IF NOT EXISTS github_username VARCHAR(100)
            """))
            conn.commit()
            print("✅ Added GitHub OAuth fields")
        except Exception as e:
            print(f"⚠️  GitHub fields might already exist: {e}")

        # Add Google OAuth fields
        try:
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS google_id VARCHAR(100) UNIQUE,
                ADD COLUMN IF NOT EXISTS google_email VARCHAR(100)
            """))
            conn.commit()
            print("✅ Added Google OAuth fields")
        except Exception as e:
            print(f"⚠️  Google fields might already exist: {e}")

        # Create indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);
                CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
            """))
            conn.commit()
            print("✅ Created OAuth indexes")
        except Exception as e:
            print(f"⚠️  Indexes might already exist: {e}")

    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate()
