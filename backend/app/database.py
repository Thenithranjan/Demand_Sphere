"""
Database Configuration Module
=============================
Configures SQLAlchemy engine and session factory for MySQL connection.
Reads credentials from .env file using python-dotenv.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ---------------------------------------------------------------------------
# Load environment variables from .env file
# ---------------------------------------------------------------------------
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ---------------------------------------------------------------------------
# Database configuration from environment
# ---------------------------------------------------------------------------
# We strip quotes in case environment variables contain extra wrapping quotes
DB_HOST = os.getenv("DB_HOST", "localhost").strip("'\"")
DB_PORT = os.getenv("DB_PORT", "3306").strip("'\"")
DB_USER = os.getenv("DB_USER", "root").strip("'\"")
DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip("'\"")
DB_NAME = os.getenv("DB_NAME", "retail_ai").strip("'\"")

# Encode the password using quote_plus to safely handle reserved URL characters like '@'
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:"
    f"{quote_plus(DB_PASSWORD)}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# TEMPORARY DEBUG PRINT: Displays the generated database URL.
# NOTE: This print is strictly for debugging the connection issue during startup and should be removed before production.
# The password is masked to prevent sensitive credentials from leaking into application logs.
print(
    f"[DEBUG] Generated DATABASE_URL (masked password): "
    f"mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    flush=True
)

# ---------------------------------------------------------------------------
# SQLAlchemy Engine & Session
# ---------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # Verify connections before use
    pool_size=10,              # Connection pool size
    max_overflow=20,           # Extra connections beyond pool_size
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Set True for SQL query logging (debug)
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Dependency Injection - Database Session
# ---------------------------------------------------------------------------
def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Ensures the session is properly closed after the request completes.

    Usage in routers:
        @router.get("/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
