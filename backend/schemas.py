"""Pydantic schemas for authentication, watchlist, portfolio, alerts,
password reset, research reports, and billing."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ── Auth ────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field("", max_length=200)
    phone: str = Field("", max_length=30)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    phone: str | None = None
    created_at: datetime | None = None
    subscription_status: str = "free"

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Password Reset ──────────────────────────────────────────────────────────

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str


# ── Watchlist ───────────────────────────────────────────────────────────────

class WatchlistAdd(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    name_en: str = Field("", max_length=200)
    name_ar: str = Field("", max_length=200)
    sector_en: str = Field("", max_length=200)
    sector_ar: str = Field("", max_length=200)
    verdict: str = Field("", max_length=50)


class WatchlistItemResponse(BaseModel):
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


# ── Portfolio ───────────────────────────────────────────────────────────────

class HoldingCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    name_en: str = Field("", max_length=200)
    name_ar: str = Field("", max_length=200)
    sector_en: str = Field("", max_length=200)
    sector_ar: str = Field("", max_length=200)
    verdict: str = Field("", max_length=50)
    quantity: float = Field(..., gt=0, description="Number of shares")
    buy_price: float = Field(..., gt=0, description="Average buy price per share")
    buy_date: datetime | None = None


class HoldingUpdate(BaseModel):
    quantity: float | None = Field(None, gt=0)
    buy_price: float | None = Field(None, gt=0)
    buy_date: datetime | None = None


class HoldingResponse(BaseModel):
    id: int
    ticker: str
    name_en: str | None = None
    name_ar: str | None = None
    sector_en: str | None = None
    sector_ar: str | None = None
    verdict: str | None = None
    quantity: float
    buy_price: float
    buy_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    total_holdings: int
    total_cost: float
    total_value: float
    total_gain_loss: float
    total_gain_loss_pct: float
    holdings: list[dict]


# ── Price Alerts ────────────────────────────────────────────────────────────

class PriceAlertCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    name_en: str = Field("", max_length=200)
    condition: str = Field(..., description="'above' or 'below'")
    target_price: float = Field(..., gt=0)


class PriceAlertResponse(BaseModel):
    id: int
    ticker: str
    name_en: str | None = None
    condition: str
    target_price: float
    triggered: bool
    triggered_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ── Research ────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    """Request body to start a research report."""
    ticker: str = Field(..., min_length=1, max_length=20)


class ResearchJobResponse(BaseModel):
    """Response when starting a research job."""
    job_id: int
    ticker: str
    status: str


class ResearchReportResponse(BaseModel):
    """Full research report with markdown content."""
    id: int
    ticker: str
    company_name: str | None = None
    status: str
    rating: str | None = None
    summary: str | None = None
    report_markdown: str | None = None
    error: str | None = None
    is_sample: bool = False
    created_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class ResearchListItem(BaseModel):
    """Brief report info for list views (no markdown content)."""
    id: int
    ticker: str
    company_name: str | None = None
    status: str
    rating: str | None = None
    summary: str | None = None
    is_sample: bool = False
    created_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


# ── Billing ─────────────────────────────────────────────────────────────────

class SubscriptionResponse(BaseModel):
    status: str = "free"
    plan: str | None = None
    current_period_end: datetime | None = None
    is_subscribed: bool = False


class CheckoutRequest(BaseModel):
    plan: str = Field("monthly", pattern="^(monthly|yearly)$")


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str
