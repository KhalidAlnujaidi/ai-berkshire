"""SQLAlchemy ORM models for user accounts and watchlists."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """Registered user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # One-to-many: user can have many watchlist items
    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")


class WatchlistItem(Base):
    """A stock saved by a user to their watchlist."""
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    name_en = Column(String, nullable=True)
    name_ar = Column(String, nullable=True)
    sector_en = Column(String, nullable=True)
    sector_ar = Column(String, nullable=True)
    verdict = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist")
