"""Pydantic schemas for authentication and watchlist endpoints."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ── Auth ────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field("", max_length=200)
    phone: str = Field("", max_length=30)


class UserLogin(BaseModel):
    """Request body for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user info returned by auth endpoints."""
    id: int
    email: str
    full_name: str | None = None
    phone: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Watchlist ───────────────────────────────────────────────────────────────

class WatchlistAdd(BaseModel):
    """Request body for adding a stock to watchlist."""
    ticker: str = Field(..., min_length=1, max_length=20)
    name_en: str = Field("", max_length=200)
    name_ar: str = Field("", max_length=200)
    sector_en: str = Field("", max_length=200)
    sector_ar: str = Field("", max_length=200)
    verdict: str = Field("", max_length=50)


class WatchlistItemResponse(BaseModel):
    """Watchlist item as returned by the API."""
    id: int
    ticker: str
    name_en: str | None = None
    name_ar: str | None = None
    sector_en: str | None = None
    sector_ar: str | None = None
    verdict: str | None = None
    added_at: datetime | None = None

    class Config:
        from_attributes = True
