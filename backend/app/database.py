"""
Database Configuration Module
=============================
Configures SQLAlchemy engine and session factory for Supabase PostgreSQL.
Reads credentials from .env file using python-dotenv.

Migration note:
    Replaces the previous MySQL/pymysql connection with a direct
    PostgreSQL connection to Supabase using psycopg2-binary.
    All downstream ORM models, CRUD functions, and FastAPI routers
    are completely unchanged — only the driver and env-var names differ.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ---------------------------------------------------------------------------
# Load environment variables from .env file (checks CWD and backend/.env)
# ---------------------------------------------------------------------------
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Supabase PostgreSQL configuration from environment
# ---------------------------------------------------------------------------
SUPABASE_DB_HOST     = os.getenv("SUPABASE_DB_HOST", "localhost").strip("'\"")
SUPABASE_DB_PORT     = os.getenv("SUPABASE_DB_PORT", "5432").strip("'\"")
SUPABASE_DB_USER     = os.getenv("SUPABASE_DB_USER", "postgres").strip("'\"")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "").strip("'\"")
SUPABASE_DB_NAME     = os.getenv("SUPABASE_DB_NAME", "postgres").strip("'\"")

from urllib.parse import quote_plus as _qp

# Try psycopg2 driver first, fallback to pg8000 if psycopg2 is unavailable
try:
    import psycopg2  # type: ignore[import]
    driver = "postgresql+psycopg2"
    connect_args = {"options": "-c statement_timeout=30000"}
except ImportError:
    try:
        import pg8000  # type: ignore[import]
        driver = "postgresql+pg8000"
        connect_args = {}
    except ImportError:
        driver = "postgresql+psycopg2"
        connect_args = {"options": "-c statement_timeout=30000"}

DATABASE_URL = (
    f"{driver}://{_qp(SUPABASE_DB_USER)}:{_qp(SUPABASE_DB_PASSWORD)}"
    f"@{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}"
    "?sslmode=require"
)

print(
    f"[INFO] Connecting to Supabase PostgreSQL: "
    f"{driver}://{SUPABASE_DB_USER}:***@"
    f"{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}",
    flush=True,
)

# ---------------------------------------------------------------------------
# SQLAlchemy Engine & Session
# ---------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Drop stale connections before use
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,    # Recycle every 30 min (Supabase idles at ~5 min)
    echo=False,
    connect_args=connect_args,
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
