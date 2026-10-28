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
    # PostgreSQL/MySQL configuration with optimized connection pool
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "20")),  # Increased from 10
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "40")),  # Increased from 20
        pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),  # Recycle after 1 hour
        pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),  # Wait 30s for connection
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
