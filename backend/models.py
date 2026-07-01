"""SQLAlchemy ORM models for user accounts, watchlists, portfolio, alerts,
password resets, research reports, and subscriptions."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text, UniqueConstraint
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Subscription / billing ──────────────────────────────────────────────
    subscription_status = Column(String, default="free", nullable=False)  # free / active / canceled
    subscription_plan = Column(String, nullable=True)  # monthly / yearly
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_period_end = Column(DateTime, nullable=True)

    # One-to-many relationships
    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    research_reports = relationship("ResearchReport", back_populates="user", cascade="all, delete-orphan")


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


class PasswordResetToken(Base):
    """Token for password reset flow.

    A token is created when a user requests a password reset.
    It expires after 1 hour and can only be used once.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")


class Holding(Base):
    """A stock holding in a user's portfolio."""
    __tablename__ = "holdings"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_holding_user_ticker"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    name_en = Column(String, nullable=True)
    name_ar = Column(String, nullable=True)
    sector_en = Column(String, nullable=True)
    sector_ar = Column(String, nullable=True)
    verdict = Column(String, nullable=True)
    quantity = Column(Float, nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="holdings")


class PriceAlert(Base):
    """A price alert set by a user."""
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    name_en = Column(String, nullable=True)
    condition = Column(String, nullable=False)  # "above" or "below"
    target_price = Column(Float, nullable=False)
    triggered = Column(Boolean, default=False, nullable=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class ResearchReport(Base):
    """An AI-generated investment research report.

    Status lifecycle: pending → running → completed | failed
    """
    __tablename__ = "research_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # nullable for sample reports
    ticker = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    report_markdown = Column(Text, nullable=True)
    summary = Column(String, nullable=True)
    rating = Column(String, nullable=True)  # STRONG_BUY / BUY / HOLD / AVOID / WATCH
    error = Column(String, nullable=True)
    is_sample = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="research_reports")
