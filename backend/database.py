"""Database engine, session, and declarative base.

Supports PostgreSQL in production (via DATABASE_URL env var) and
SQLite for local development (fallback).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Database URL ────────────────────────────────────────────────────────────
# Production:  DATABASE_URL=postgresql://user:pass@host:port/dbname
# Development: falls back to local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mizan.db")

# SQLite needs special connect args (check_same_thread) because FastAPI
# can use multiple threads for sync endpoints.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
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
    """Create all tables. Called on startup."""
    # Import models so they register with Base.metadata
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
