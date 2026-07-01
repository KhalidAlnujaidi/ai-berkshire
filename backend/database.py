"""Database engine, session, and declarative base.

Supports PostgreSQL in production (via DATABASE_URL env var) and
SQLite for local development (fallback).

Production connection pool settings are tuned for FastAPI sync endpoints
running behind Gunicorn with multiple Uvicorn workers.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# ── Database URL ────────────────────────────────────────────────────────────
# Production:  DATABASE_URL=postgresql://user:pass@host:port/dbname
# Development: falls back to local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mizan.db")

# SQLite needs special connect args (check_same_thread) because FastAPI
# can use multiple threads for sync endpoints.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# ── Connection pool tuning (PostgreSQL only; SQLite uses SingletonThreadPool) ──
_engine_kwargs = {"connect_args": connect_args, "echo": False}

if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update({
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_pre_ping": True,   # detect stale connections before use
        "pool_recycle": 1800,    # recycle connections every 30 minutes
    })

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a database session, closes it after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on startup.

    NOTE: For production schema changes, use Alembic migrations instead of
    relying on create_all. This is fine for initial table creation.
    """
    import models  # noqa: F401 — register models with Base.metadata
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
