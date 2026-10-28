#!/bin/bash
# One-line fix for database configuration
# Usage: curl -sSL https://raw.githubusercontent.com/.../quick_fix.sh | bash
# Or: bash quick_fix.sh

set -e

echo "🔧 Nautilus Database Configuration Quick Fix"
echo ""

# Backup
echo "📦 Creating backup..."
cp utils/database.py utils/database.py.backup.$(date +%Y%m%d_%H%M%S)

# Apply fix
echo "✏️  Applying fix..."
cat > utils/database.py << 'EOF'
"""
Database configuration and session management.
"""
from dotenv import load_dotenv

# Load environment variables BEFORE any configuration
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os

from models.database import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nautilus.db")

# Create engine with SQLite-specific configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
        pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Usage:
        from utils.database import get_db

        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Get database session as context manager.

    Usage:
        from utils.database import get_db_context

        with get_db_context() as db:
            items = db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """Get database engine instance."""
    return engine
EOF

echo "✅ Fix applied"
echo ""
echo "🔄 Restarting service..."
sudo systemctl restart nautilus-backend

echo "⏳ Waiting for service to start..."
sleep 3

echo "🏥 Testing health check..."
HEALTH=$(curl -s http://localhost:8000/health || echo "failed")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Service is healthy!"
    echo "$HEALTH"
else
    echo "⚠️  Health check response: $HEALTH"
fi

echo ""
echo "✅ Fix complete!"
echo ""
echo "Next steps:"
echo "  - Check logs: sudo journalctl -u nautilus-backend -f"
echo "  - Verify database: psql -U postgres -d nautilus -c '\dt'"
echo "  - Rollback if needed: cp utils/database.py.backup.* utils/database.py"
