"""
Verify database configuration is correctly loaded.
"""
import sys
from utils.database import DATABASE_URL, engine

def verify_database_config():
    """Verify database configuration."""
    print("=" * 60)
    print("Database Configuration Verification")
    print("=" * 60)

    # Check DATABASE_URL
    print(f"\n1. DATABASE_URL: {DATABASE_URL}")

    # Check database type
    if DATABASE_URL.startswith("postgresql"):
        print("   ✓ Using PostgreSQL")
    elif DATABASE_URL.startswith("sqlite"):
        print("   ✗ Using SQLite (should be PostgreSQL)")
        return False
    else:
        print(f"   ? Unknown database type")
        return False

    # Check engine
    print(f"\n2. Engine: {engine}")
    print(f"   Driver: {engine.driver}")
    print(f"   URL: {engine.url}")

    # Test connection
    print("\n3. Testing connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"   ✓ Connection successful")
            print(f"   PostgreSQL version: {version}")
            return True
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_database_config()
    print("\n" + "=" * 60)
    if success:
        print("✓ Database configuration is correct")
        sys.exit(0)
    else:
        print("✗ Database configuration has issues")
        sys.exit(1)
