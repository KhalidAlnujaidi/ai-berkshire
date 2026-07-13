"""Mizan Backend API — FastAPI application.

Wraps the sharia_screener.py engine as a REST API for the Mizan web app.
Provides:
  - GET  /api/health          — health check
  - GET  /api/stocks          — list all stocks in database
  - GET  /api/stocks/{ticker} — get single stock + Sharia verdict
  - GET  /api/halal-stocks    — list ONLY Sharia-compliant stocks (pre-filtered)
  - POST /api/sharia-screen   — screen a company with custom financial data
  - POST /api/portfolio-screen — screen an entire portfolio (multiple holdings)
  - GET  /api/search?q=...    — search stocks by name or ticker (with verdict)

Authentication (new):
  - POST /api/auth/register   — create a new user account
  - POST /api/auth/login      — authenticate and receive JWT
  - GET  /api/auth/me         — get current user info

Watchlist (new, requires auth):
  - GET    /api/watchlist        — list user's watchlist
  - POST   /api/watchlist        — add a stock to watchlist
  - DELETE /api/watchlist/{ticker} — remove a stock from watchlist
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional

import logging
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# ── Import the Sharia screener ──────────────────────────────────────────────
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from sharia_screener import screen_company, screen_sector  # noqa: E402


from database import get_db, init_db, engine
from models import User, WatchlistItem, PasswordResetToken, Holding, PriceAlert
from auth import (
    hash_password, verify_password, create_access_token,
    decode_access_token, get_current_user, get_optional_user,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# ── SSE streaming for agent pipeline progress ──────────────────────────────
from sse_starlette.sse import EventSourceResponse
import asyncio
from schemas import (
    WatchlistAdd, WatchlistItemResponse,
    PasswordResetRequest, PasswordResetConfirm,
    PasswordChangeRequest, MessageResponse,
    HoldingCreate, HoldingUpdate, HoldingResponse,
    PriceAlertCreate, PriceAlertResponse,
    TokenResponse, UserRegister, UserLogin, UserResponse,
)
from email_service import send_password_reset_email, send_alert_notification_email
from stock_data import get_price, get_prices_bulk, get_price_history, clear_cache as clear_price_cache
import tadawul_scraper
from metrics import metrics_middleware, metrics_endpoint, PROMETHEUS_AVAILABLE

# ── Research engine & billing ────────────────────────────────────────────────
from fastapi import BackgroundTasks
from models import ResearchReport
from schemas import (
    ResearchRequest, ResearchJobResponse, ResearchReportResponse,
    ResearchListItem,
    SubscriptionResponse, CheckoutRequest, CheckoutResponse,
    PortalResponse,
)
import research_engine
import stripe_service
# ── Stock Database ──────────────────────────────────────────────────────────
STOCKS_FILE = Path(__file__).resolve().parent / "stocks.json"

def load_stocks() -> list[dict]:
    """Load Saudi stock data from JSON file."""
    with open(STOCKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def find_stock(query: str) -> Optional[dict]:
    """Find a stock by ticker or name (Arabic or English)."""
    stocks = load_stocks()
    q = query.strip().lower()

    # Try exact ticker match first
    for stock in stocks:
        if stock["ticker"] == query.strip():
            return stock

    # Try Arabic name match
    for stock in stocks:
        if query.strip() in stock.get("name_ar", ""):
            return stock

    # Try English name match (case-insensitive substring)
    for stock in stocks:
        if q in stock.get("name_en", "").lower():
            return stock

    return None

def screen_stock(stock: dict) -> dict:
    """Run the Sharia screen on a single stock dict and merge results."""
    result = screen_company(
        name=stock["name_en"],
        ticker=stock["ticker"],
        sector=stock["sector_en"],
        total_assets=stock["total_assets"],
        total_debt=stock["total_debt"],
        interest_bearing_investments=stock.get("interest_bearing_investments", 0),
        accounts_receivable=stock.get("accounts_receivable", 0),
        cash_and_equivalents=stock.get("cash_and_equivalents", 0),
        market_cap=stock.get("market_cap", 0),
        non_compliant_income=stock.get("non_compliant_income", 0),
        total_revenue=stock.get("total_revenue", 0),
    )
    return {
        **result,
        "name_ar": stock["name_ar"],
        "sector_ar": stock["sector_ar"],
        "market": stock.get("market", "saudi"),
        "currency": stock.get("currency", "SAR"),
    }

# ── Rate Limiting ───────────────────────────────────────────────────────────
# Fail-soft: limits are enforced but app still runs if Redis is unavailable.
limiter = Limiter(key_func=get_remote_address)

# ── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mizan API",
    description="Sharia-compliant investment screening API for Saudi Arabia",
    version="2.0.0",
)

logger = logging.getLogger(__name__)

# Wire rate limiter into app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS — configurable via env ─────────────────────────────────────────────
# Comma-separated list of allowed origins. Defaults cover local dev.
_default_origins = "http://localhost:3000,http://localhost:3001"
_cors_env = os.getenv("CORS_ORIGINS", _default_origins)
allow_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
# In production also allow explicit Vercel/自定义 domains
_prod_origins = os.getenv("ALLOWED_ORIGINS", "")
if _prod_origins:
    allow_origins.extend([o.strip() for o in _prod_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS origins: {allow_origins}")

# ── Prometheus metrics middleware ──
app.middleware("http")(metrics_middleware)


# ── Structured error handling ───────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a clean 500 response.

    Prevents stack traces from leaking to the client in production.
    """
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Initialize database on startup ─────────────────────────────────────────
@app.on_event("startup")
def startup():
    """Create database tables on startup."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    init_db()

    # Seed demo research reports (fail-soft)
    try:
        from database import SessionLocal
        _seed_db = SessionLocal()
        research_engine.seed_sample_reports(_seed_db)
        _seed_db.close()
    except Exception as e:
        logger.warning(f"Could not seed sample reports: {e}")

    logger.info(f"Mizan API started — {len(load_stocks())} stocks loaded")
class ShariaScreenRequest(BaseModel):
    """Request body for custom Sharia screening."""
    name: str = Field(..., description="Company name")
    ticker: str = Field("", description="Stock ticker symbol")
    sector: str = Field("", description="Business sector")
    total_assets: float = Field(..., gt=0, description="Total assets in SAR")
    total_debt: float = Field(0, ge=0, description="Total interest-bearing debt")
    interest_bearing_investments: float = Field(0, ge=0)
    accounts_receivable: float = Field(0, ge=0)
    cash_and_equivalents: float = Field(0, ge=0)
    market_cap: float = Field(0, ge=0)
    non_compliant_income: float = Field(0, ge=0)
    total_revenue: float = Field(0, ge=0)

class PortfolioHolding(BaseModel):
    """A single holding in a portfolio screening request."""
    ticker: str = Field(..., description="Stock ticker symbol")
    amount: float = Field(..., gt=0, description="Investment amount in the holding's currency")

class PortfolioScreenRequest(BaseModel):
    """Request body for portfolio Sharia screening."""
    holdings: list[PortfolioHolding] = Field(..., min_length=1, description="Portfolio holdings")

class StockBrief(BaseModel):
    """Brief stock info for list/search responses."""
    ticker: str
    name_ar: str
    name_en: str
    sector_ar: str
    sector_en: str


# ════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/auth/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, req: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account and return a JWT token."""
    # Check if email already taken
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )

    # Create user
    user = User(
        email=req.email,
        full_name=req.full_name or None,
        phone=req.phone or None,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, req: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@app.get("/api/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


# ── Google OAuth ──────────────────────────────────────────────────────────────


from google_oauth import (
    enabled as google_oauth_enabled,
    get_authorization_url,
    exchange_code,
    get_user_info,
    FRONTEND_URL,
)
from fastapi.responses import RedirectResponse, HTMLResponse


@app.get("/api/auth/google")
def google_oauth_authorize(request: Request):
    """Redirect the user to Google's OAuth consent screen.

    If Google OAuth is not configured, returns a 501 with instructions.
    """
    if not google_oauth_enabled:
        return HTMLResponse(
            content="""
            <html><body style="font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh">
            <div style="text-align:center"><h1>Google Login Not Configured</h1>
            <p>Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in the server environment.</p>
            <a href="/">Back to Home</a></div></body></html>
            """,
            status_code=501,
        )

    state = _secrets.token_urlsafe(32)
    # Store state in a short-lived session / cookie so we can verify it on callback
    auth_url = get_authorization_url(state=state)
    redirect = RedirectResponse(url=auth_url, status_code=302)
    redirect.set_cookie(
        key="oauth_state",
        value=state,
        max_age=300,       # 5 minutes
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return redirect


@app.get("/api/auth/google/callback")
def google_oauth_callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
    db: Session = Depends(get_db),
):
    """Handle the Google OAuth callback.

    On success, redirects to the frontend with a JWT token in the URL:
        /login?token=xxx

    On error, redirects to the frontend login page with an error:
        /login?error=xxx
    """
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/{request.cookies.get('locale', 'en')}/login?error=access_denied",
            status_code=302,
        )

    if not google_oauth_enabled:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/{request.cookies.get('locale', 'en')}/login?error=not_configured",
            status_code=302,
        )

    # Verify state to prevent CSRF
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/{request.cookies.get('locale', 'en')}/login?error=invalid_state",
            status_code=302,
        )

    # Exchange code for tokens
    tokens = exchange_code(code)
    if not tokens or "access_token" not in tokens:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/{request.cookies.get('locale', 'en')}/login?error=token_exchange_failed",
            status_code=302,
        )

    # Fetch user info
    google_user = get_user_info(tokens["access_token"])
    if not google_user or "email" not in google_user:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/{request.cookies.get('locale', 'en')}/login?error=userinfo_failed",
            status_code=302,
        )

    email = google_user["email"].lower().strip()
    name = google_user.get("name", "")

    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Auto-register with Google account
        user = User(
            email=email,
            full_name=name or None,
            hashed_password="__oauth__google__",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate JWT
    jwt_token = create_access_token({"sub": str(user.id)})

    # Redirect to frontend with token
    locale = request.cookies.get("locale", "en")
    return RedirectResponse(
        url=f"{FRONTEND_URL}/{locale}/login?token={jwt_token}",
        status_code=302,
    )


# ════════════════════════════════════════════════════════════════════════════
# PASSWORD RESET ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

import secrets as _secrets
import hashlib as _hashlib
from datetime import datetime as _dt, timedelta as _td


def _hash_reset_token(token: str) -> str:
    """SHA-256 hash a reset token for storage. We never store raw tokens."""
    return _hashlib.sha256(token.encode()).hexdigest()


@app.post("/api/auth/password-reset/request", response_model=MessageResponse)
@limiter.limit("3/minute")
def request_password_reset(
    request: Request, req: PasswordResetRequest, db: Session = Depends(get_db)
):
    """Initiate a password reset.

    Always returns 200 ("If the email exists, a reset link has been sent")
    regardless of whether the email exists — prevents email enumeration.
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        return MessageResponse(message="If the email exists, a reset link has been sent.")

    # Invalidate any existing tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": _dt.utcnow()})

    # Generate a cryptographically secure token
    raw_token = _secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(raw_token)
    expires_at = _dt.utcnow() + _td(hours=1)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_record)
    db.commit()

    # Send email (fail-soft: don't fail the request if email fails)
    try:
        send_password_reset_email(user.email, raw_token, user.full_name)
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")

    return MessageResponse(message="If the email exists, a reset link has been sent.")


@app.post("/api/auth/password-reset/confirm", response_model=MessageResponse)
@limiter.limit("5/minute")
def confirm_password_reset(
    request: Request, req: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """Complete a password reset using a valid token."""
    token_hash = _hash_reset_token(req.token)
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid reset token.")
    if record.used_at is not None:
        raise HTTPException(status_code=400, detail="This reset token has already been used.")
    if record.expires_at < _dt.utcnow():
        raise HTTPException(status_code=400, detail="This reset token has expired.")

    # Update password
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token.")

    user.hashed_password = hash_password(req.new_password)
    record.used_at = _dt.utcnow()
    db.commit()

    return MessageResponse(message="Your password has been reset successfully.")


@app.post("/api/auth/change-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def change_password(
    request: Request,
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password for an authenticated user."""
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()

    return MessageResponse(message="Your password has been changed successfully.")


# ════════════════════════════════════════════════════════════════════════════
# WATCHLIST ENDPOINTS (requires authentication)
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/watchlist", response_model=list[WatchlistItemResponse])
def get_watchlist(current_user: User = Depends(get_current_user)):
    """Get the current user's watchlist."""
    items = current_user.watchlist
    return [WatchlistItemResponse.model_validate(item) for item in items]


@app.post("/api/watchlist", response_model=WatchlistItemResponse)
def add_to_watchlist(
    item: WatchlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a stock to the current user's watchlist.

    If the stock is already in the watchlist, returns the existing item
    (idempotent — no error).
    """
    # Check if already exists
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.ticker == item.ticker,
    ).first()

    if existing:
        return WatchlistItemResponse.model_validate(existing)

    # Create new
    wl_item = WatchlistItem(
        user_id=current_user.id,
        ticker=item.ticker,
        name_en=item.name_en or None,
        name_ar=item.name_ar or None,
        sector_en=item.sector_en or None,
        sector_ar=item.sector_ar or None,
        verdict=item.verdict or None,
    )
    db.add(wl_item)
    db.commit()
    db.refresh(wl_item)

    return WatchlistItemResponse.model_validate(wl_item)


@app.delete("/api/watchlist/{ticker}")
def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a stock from the current user's watchlist."""
    item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.ticker == ticker,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"'{ticker}' not in watchlist")

    db.delete(item)
    db.commit()



# ════════════════════════════════════════════════════════════════════════════
# PORTFOLIO ENDPOINTS (requires auth)
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/portfolio")
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's portfolio with live price enrichment."""
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()

    if not holdings:
        return {
            "total_holdings": 0,
            "total_cost": 0,
            "total_value": 0,
            "total_gain_loss": 0,
            "total_gain_loss_pct": 0,
            "holdings": [],
        }

    # Fetch live prices for all holdings in one batch
    tickers = [h.ticker for h in holdings]
    prices = get_prices_bulk(tickers)

    enriched = []
    total_cost = 0.0
    total_value = 0.0

    for h in holdings:
        cost = h.quantity * h.buy_price
        live = prices.get(h.ticker)
        current_price = live.get("price") if live else None
        value = h.quantity * current_price if current_price else cost
        gain_loss = value - cost
        gain_loss_pct = (gain_loss / cost * 100) if cost > 0 else 0

        total_cost += cost
        total_value += value

        enriched.append({
            "id": h.id,
            "ticker": h.ticker,
            "name_en": h.name_en,
            "name_ar": h.name_ar,
            "sector_en": h.sector_en,
            "sector_ar": h.sector_ar,
            "verdict": h.verdict,
            "quantity": h.quantity,
            "buy_price": h.buy_price,
            "buy_date": h.buy_date.isoformat() if h.buy_date else None,
            "current_price": current_price,
            "market_value": round(value, 2),
            "cost_basis": round(cost, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
            "day_change_pct": live.get("day_change_pct") if live else None,
        })

    total_gain = total_value - total_cost
    total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0

    return {
        "total_holdings": len(holdings),
        "total_cost": round(total_cost, 2),
        "total_value": round(total_value, 2),
        "total_gain_loss": round(total_gain, 2),
        "total_gain_loss_pct": round(total_gain_pct, 2),
        "holdings": enriched,
    }


@app.post("/api/portfolio", response_model=HoldingResponse)
def add_holding(
    holding: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a stock to the portfolio (upsert — if ticker exists, quantity averages)."""
    existing = db.query(Holding).filter(
        Holding.user_id == current_user.id,
        Holding.ticker == holding.ticker,
    ).first()

    if existing:
        # Average the buy price weighted by quantity
        total_qty = existing.quantity + holding.quantity
        avg_price = (
            (existing.quantity * existing.buy_price) + (holding.quantity * holding.buy_price)
        ) / total_qty
        existing.quantity = total_qty
        existing.buy_price = round(avg_price, 4)
        if holding.buy_date:
            existing.buy_date = holding.buy_date
        db.commit()
        db.refresh(existing)
        return HoldingResponse.model_validate(existing)

    new_holding = Holding(
        user_id=current_user.id,
        ticker=holding.ticker,
        name_en=holding.name_en or None,
        name_ar=holding.name_ar or None,
        sector_en=holding.sector_en or None,
        sector_ar=holding.sector_ar or None,
        verdict=holding.verdict or None,
        quantity=holding.quantity,
        buy_price=holding.buy_price,
        buy_date=holding.buy_date,
    )
    db.add(new_holding)
    db.commit()
    db.refresh(new_holding)
    return HoldingResponse.model_validate(new_holding)


@app.put("/api/portfolio/{ticker}", response_model=HoldingResponse)
def update_holding(
    ticker: str,
    update: HoldingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a holding's quantity, buy price, or buy date."""
    holding = db.query(Holding).filter(
        Holding.user_id == current_user.id,
        Holding.ticker == ticker,
    ).first()

    if not holding:
        raise HTTPException(status_code=404, detail=f"Holding '{ticker}' not found")

    if update.quantity is not None:
        holding.quantity = update.quantity
    if update.buy_price is not None:
        holding.buy_price = update.buy_price
    if update.buy_date is not None:
        holding.buy_date = update.buy_date

    db.commit()
    db.refresh(holding)
    return HoldingResponse.model_validate(holding)


@app.delete("/api/portfolio/{ticker}")
def remove_holding(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a holding from the portfolio."""
    holding = db.query(Holding).filter(
        Holding.user_id == current_user.id,
        Holding.ticker == ticker,
    ).first()

    if not holding:
        raise HTTPException(status_code=404, detail=f"Holding '{ticker}' not found")

    db.delete(holding)
    db.commit()
    return {"status": "removed", "ticker": ticker}


# ════════════════════════════════════════════════════════════════════════════
# PRICE ALERT ENDPOINTS (requires auth)
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/alerts", response_model=list[PriceAlertResponse])
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all price alerts for the current user."""
    alerts = db.query(PriceAlert).filter(
        PriceAlert.user_id == current_user.id,
    ).order_by(PriceAlert.created_at.desc()).all()
    return [PriceAlertResponse.model_validate(a) for a in alerts]


@app.post("/api/alerts", response_model=PriceAlertResponse)
@limiter.limit("10/minute")
def create_alert(
    request: Request,
    alert: PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new price alert."""
    if alert.condition not in ("above", "below"):
        raise HTTPException(status_code=422, detail="condition must be 'above' or 'below'")

    new_alert = PriceAlert(
        user_id=current_user.id,
        ticker=alert.ticker,
        name_en=alert.name_en or None,
        condition=alert.condition,
        target_price=alert.target_price,
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return PriceAlertResponse.model_validate(new_alert)


@app.delete("/api/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a price alert."""
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id,
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()
    return {"status": "removed", "alert_id": alert_id}


@app.post("/api/alerts/check")
def check_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check all active (non-triggered) alerts against current prices.

    Returns a list of newly triggered alerts.
    """
    active = db.query(PriceAlert).filter(
        PriceAlert.user_id == current_user.id,
        PriceAlert.triggered == False,
    ).all()

    if not active:
        return {"checked": 0, "triggered": []}

    tickers = list({a.ticker for a in active})
    prices = get_prices_bulk(tickers)
    newly_triggered = []

    for alert in active:
        live = prices.get(alert.ticker)
        if not live or live.get("price") is None:
            continue

        current = live["price"]
        hit = (
            (alert.condition == "above" and current >= alert.target_price)
            or (alert.condition == "below" and current <= alert.target_price)
        )

        if hit:
            alert.triggered = True
            alert.triggered_at = _dt.utcnow()
            newly_triggered.append({
                "alert_id": alert.id,
                "ticker": alert.ticker,
                "name_en": alert.name_en,
                "condition": alert.condition,
                "target_price": alert.target_price,
                "current_price": current,
            })

    if newly_triggered:
        db.commit()
        # Send email notification (fail-soft — never break the API)
        try:
            send_alert_notification_email(
                current_user.email,
                current_user.full_name or "",
                newly_triggered,
            )
        except Exception as e:
            logger.warning(f"Failed to send alert notification email to {current_user.email}: {e}")

    return {"checked": len(active), "triggered": newly_triggered}

# ════════════════════════════════════════════════════════════════════════════
# STOCK SCREENING ENDPOINTS (existing — unchanged)
# ════════════════════════════════════════════════════════════════════════════

@app.get("/metrics")
async def prometheus_metrics(request: Request):
    """Prometheus metrics endpoint for monitoring."""
    return await metrics_endpoint(request)

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    stocks = load_stocks()
    return {
        "status": "ok",
        "service": "Mizan Sharia Screening API",
        "version": "2.0.0",
        "standard": "AAOIFI Standard No. 21",
        "stocks_count": len(stocks),
        "auth": "enabled",
    }

@app.get("/api/stocks")
async def list_stocks(sector: Optional[str] = None):
    """List all stocks in the database, optionally filtered by sector."""
    stocks = load_stocks()

    if sector:
        sector_lower = sector.lower()
        stocks = [
            s for s in stocks
            if sector_lower in s.get("sector_en", "").lower()
            or sector in s.get("sector_ar", "")
        ]

    # Return brief info without financial details
    return [
        StockBrief(
            ticker=s["ticker"],
            name_ar=s["name_ar"],
            name_en=s["name_en"],
            sector_ar=s["sector_ar"],
            sector_en=s["sector_en"],
        )
        for s in stocks
    ]

@app.get("/api/halal-stocks")
async def list_halal_stocks(sector: Optional[str] = None):
    """List ONLY Sharia-compliant stocks.

    Every stock in the database is screened on the fly. Only those that
    pass BOTH qualitative and quantitative screens are returned. This is
    the core 'Discover' feature — users browse a pre-filtered universe
    where every stock is already verified halal.
    """
    stocks = load_stocks()

    if sector:
        sector_lower = sector.lower()
        stocks = [
            s for s in stocks
            if sector_lower in s.get("sector_en", "").lower()
            or sector in s.get("sector_ar", "")
        ]

    halal_only = []
    for s in stocks:
        result = screen_stock(s)
        verdict = result.get("verdict", "")
        if verdict in ("COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
            halal_only.append({
                "ticker": s["ticker"],
                "name_en": s["name_en"],
                "name_ar": s["name_ar"],
                "sector_en": s["sector_en"],
                "sector_ar": s["sector_ar"],
                "market": s.get("market", "saudi"),
                "currency": s.get("currency", "SAR"),
                "verdict": verdict,
                "verdict_detail": result.get("verdict_detail", ""),
            })

    return {
        "count": len(halal_only),
        "total_screened": len(stocks),
        "stocks": halal_only,
    }

@app.get("/api/stocks/{ticker}")
async def get_stock(ticker: str):
    """Get a single stock with full Sharia compliance screening."""
    stock = find_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found")

    return screen_stock(stock)

# ════════════════════════════════════════════════════════════════════════════
# LIVE PRICE ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/stocks/{ticker}/price")
async def get_stock_price(ticker: str):
    """Get live market price for a stock.

    Fetches from Yahoo Finance with caching (5-min TTL).
    Fails soft: returns stale cached data if Yahoo is unreachable.
    """
    stock = find_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found")

    price_data = get_price(ticker)
    if price_data is None:
        raise HTTPException(
            status_code=503,
            detail="Price data temporarily unavailable. Please try again later.",
        )

    return {
        **price_data,
        "ticker": ticker,
        "name_en": stock["name_en"],
        "name_ar": stock["name_ar"],
    }


@app.get("/api/prices")
async def get_market_prices(
    tickers: str = Query("", description="Comma-separated tickers (max 20). Empty = all halal stocks."),
):
    """Get live prices for multiple stocks.

    With no `tickers` param, returns prices for all Sharia-compliant stocks.
    Fails soft: missing tickers are omitted from results.
    """
    all_stocks = load_stocks()

    if tickers.strip():
        requested = [t.strip() for t in tickers.split(",") if t.strip()][:20]
    else:
        # Default: all halal stocks
        requested = []
        for s in all_stocks:
            result = screen_stock(s)
            if result.get("verdict") in ("COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
                requested.append(s["ticker"])

    prices = get_prices_bulk(requested)

    # Build response with stock names
    stock_map = {s["ticker"]: s for s in all_stocks}
    results = []
    for t in requested:
        if t in prices:
            s = stock_map.get(t, {})
            results.append({
                **prices[t],
                "name_en": s.get("name_en", ""),
                "name_ar": s.get("name_ar", ""),
            })

    return {
        "count": len(results),
        "requested": len(requested),
        "prices": results,
    }


@app.post("/api/prices/refresh")
async def refresh_prices(
    request: Request,
    ticker: Optional[str] = Query(None, description="Single ticker to refresh, or all"),
):
    """Clear the price cache, forcing fresh data on next request.

    Rate-limited to prevent abuse. Internal/monitoring endpoint.
    """
    clear_price_cache(ticker)
    scope = f"'{ticker}'" if ticker else "all tickers"
    logger.info(f"Price cache cleared for {scope} by {request.client.host if request.client else 'unknown'}")
    return {"status": "ok", "message": f"Cache cleared for {scope}"}

# ── Tadawul direct scraping endpoints ─────────────────────────────────────────
# These endpoints fetch live data directly from Saudi Exchange (saudiexchange.sa)
# via Playwright. Each scrape session takes ~6-7s; results are cached 5 minutes.

@app.get("/api/tadawul/prices")
@limiter.limit("30/minute")
async def tadawul_all_prices(
    request: Request,
    ticker: Optional[str] = Query(None, description="Filter to a single ticker"),
    halal_only: bool = Query(False, description="Only return Sharia-compliant stocks"),
):
    """Get live market data for all Tadawul-listed instruments via direct scrape.

    Each scrape takes ~6s; results are cached for 5 minutes.
    Fails soft: returns stale cached data if the scrape fails.
    """
    prices = tadawul_scraper.get_all_stock_prices()
    if prices is None:
        raise HTTPException(
            status_code=503,
            detail="Tadawul data temporarily unavailable. Please try again later.",
        )

    if ticker:
        t = ticker.strip()
        single = prices.get(t)
        if single is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{t}' not found on Tadawul")
        return {"count": 1, "prices": [single], "cached": prices.get("cached", False), "stale": prices.get("stale", False)}

    # Optionally filter to halal stocks only
    halal_tickers = None
    if halal_only:
        halal_tickers = {
            s["ticker"] for s in load_stocks()
            if screen_stock(s).get("verdict", "").startswith("COMPLIANT")
        }

    result_list = [
        v for v in prices.values()
        if not halal_tickers or v.get("ticker") in halal_tickers
    ]

    return {
        "count": len(result_list),
        "cached": prices.get("cached", False),
        "stale": prices.get("stale", False),
        "prices": result_list,
    }


@app.get("/api/tadawul/prices/{ticker}")
@limiter.limit("60/minute")
async def tadawul_single_price(ticker: str, request: Request):
    """Get live market data for a single Tadawul instrument."""
    price = tadawul_scraper.get_stock_price(ticker)
    if price is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{ticker}' not found on Tadawul, or data temporarily unavailable.",
        )
    return price


@app.get("/api/tadawul/summary")
@limiter.limit("30/minute")
async def tadawul_market_summary(request: Request):
    """Get TASI/MT30/NomuC/Sukuk index data, advancers/decliners, and market status.

    Direct scrape from Saudi Exchange. Cached 5 minutes.
    """
    summary = tadawul_scraper.get_market_summary()
    if summary is None:
        raise HTTPException(
            status_code=503,
            detail="Tadawul market summary temporarily unavailable.",
        )
    return summary


@app.get("/api/tadawul/companies")
@limiter.limit("20/minute")
async def tadawul_company_directory(
    request: Request,
    market_type: Optional[str] = Query(None, description="Filter by market: M=Main, S=NomuC, B=Sukuk, D=Derivative"),
    q: str = Query("", description="Search by name or symbol"),
):
    """Get the full Tadawul company directory (1871 instruments).

    Filter by market type or search by name/symbol.
    Cached 5 minutes.
    """
    companies = tadawul_scraper.get_company_directory()
    if companies is None:
        raise HTTPException(
            status_code=503,
            detail="Tadawul company directory temporarily unavailable.",
        )

    if market_type:
        companies = [c for c in companies if c.get("market_type") == market_type]

    if q.strip():
        ql = q.strip().lower()
        companies = [
            c for c in companies
            if ql in c.get("symbol", "").lower()
            or ql in c.get("name_en", "").lower()
            or ql in c.get("name_ar", "")
            or ql in c.get("trading_name_en", "").lower()
            or ql in c.get("trading_name_ar", "")
        ]

    return {
        "count": len(companies),
        "cached": any(isinstance(c, dict) and c.get("cached") for c in companies if isinstance(c, dict)),
        "companies": companies,
    }


@app.post("/api/tadawul/cache/refresh")
async def tadawul_refresh_cache(request: Request):
    """Clear the Tadawul scraper cache, forcing fresh data on next request."""
    tadawul_scraper.clear_cache()
    logger.info(f"Tadawul cache cleared by {request.client.host if request.client else 'unknown'}")
    return {"status": "ok", "message": "Tadawul cache cleared"}


@app.post("/api/sharia-screen")
async def custom_sharia_screen(req: ShariaScreenRequest):
    """Screen a custom company with user-provided financial data."""
    result = screen_company(
        name=req.name,
        ticker=req.ticker,
        sector=req.sector,
        total_assets=req.total_assets,
        total_debt=req.total_debt,
        interest_bearing_investments=req.interest_bearing_investments,
        accounts_receivable=req.accounts_receivable,
        cash_and_equivalents=req.cash_and_equivalents,
        market_cap=req.market_cap,
        non_compliant_income=req.non_compliant_income,
        total_revenue=req.total_revenue,
    )
    return result

@app.post("/api/portfolio-screen")
async def screen_portfolio(req: PortfolioScreenRequest):
    """Screen an entire investment portfolio for Sharia compliance."""
    holdings_results = []
    total_amount = 0.0
    halal_amount = 0.0
    purification_amount = 0.0
    non_compliant_amount = 0.0
    not_found = []

    for holding in req.holdings:
        stock = find_stock(holding.ticker)
        if not stock:
            not_found.append(holding.ticker)
            continue

        result = screen_stock(stock)
        verdict = result.get("verdict", "NON_COMPLIANT")
        total_amount += holding.amount

        if verdict == "COMPLIANT":
            halal_amount += holding.amount
        elif verdict in ("COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
            halal_amount += holding.amount
            purification_amount += holding.amount
        else:
            non_compliant_amount += holding.amount

        holdings_results.append({
            "ticker": holding.ticker,
            "name_en": stock["name_en"],
            "name_ar": stock["name_ar"],
            "sector_en": stock["sector_en"],
            "sector_ar": stock["sector_ar"],
            "amount": holding.amount,
            "currency": stock.get("currency", "SAR"),
            "verdict": verdict,
            "verdict_ar": result.get("verdict_ar", ""),
            "verdict_detail": result.get("verdict_detail", ""),
            "is_halal": verdict in ("COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"),
            "needs_purification": verdict in ("COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"),
            "weight_pct": 0,
        })

    for h in holdings_results:
        h["weight_pct"] = round(h["amount"] / total_amount * 100, 2) if total_amount > 0 else 0

    halal_pct = round(halal_amount / total_amount * 100, 2) if total_amount > 0 else 0
    non_compliant_pct = round(non_compliant_amount / total_amount * 100, 2) if total_amount > 0 else 0
    purification_pct = round(purification_amount / total_amount * 100, 2) if total_amount > 0 else 0

    if non_compliant_pct > 50:
        grade = "HIGH_RISK"
        grade_ar = "محفظة عالية المخاطر"
    elif non_compliant_pct > 20:
        grade = "NEEDS_REBALANCING"
        grade_ar = "تحتاج إلى إعادة توازن"
    elif purification_pct > 30:
        grade = "PURIFICATION_REQUIRED"
        grade_ar = "يلزم تنقية الدخل"
    else:
        grade = "SHARIA_COMPLIANT"
        grade_ar = "متوافقة مع الشريعة"

    recommendations = []
    if non_compliant_amount > 0:
        nc_count = len([h for h in holdings_results if h["verdict"] == "NON_COMPLIANT"])
        recommendations.append({
            "type": "SELL",
            "title_en": f"Exit {nc_count} non-compliant holding(s)",
            "title_ar": f"تخارج من {nc_count} استثمار غير متوافق",
            "detail_en": f"{non_compliant_amount:,.0f} ({non_compliant_pct}%) of your portfolio is in non-compliant stocks.",
            "detail_ar": f"{non_compliant_amount:,.0f} ({non_compliant_pct}%) من محفظتك في أسهم غير متوافقة.",
            "severity": "critical",
        })
    if purification_amount > 0:
        pur_count = len([h for h in holdings_results if h["needs_purification"]])
        recommendations.append({
            "type": "PURIFY",
            "title_en": f"Purify income from {pur_count} holding(s)",
            "title_ar": f"نقّ دخل {pur_count} استثمار",
            "detail_en": f"{purification_amount:,.0f} ({purification_pct}%) of your portfolio requires income purification.",
            "detail_ar": f"{purification_amount:,.0f} ({purification_pct}%) من محفظتك يتطلب تنقية الدخل.",
            "severity": "warning",
        })
    if non_compliant_pct == 0 and purification_pct == 0:
        recommendations.append({
            "type": "GOOD",
            "title_en": "Your portfolio is fully Sharia-compliant",
            "title_ar": "محفظتك متوافقة بالكامل مع الشريعة",
            "detail_en": "All holdings pass both qualitative and quantitative Sharia screens.",
            "detail_ar": "جميع الاستثمارات تجتاز الفحصين النوعي والكمي.",
            "severity": "success",
        })

    return {
        "holdings": holdings_results,
        "summary": {
            "total_holdings": len(holdings_results),
            "total_amount": total_amount,
            "halal_amount": halal_amount,
            "halal_pct": halal_pct,
            "non_compliant_amount": non_compliant_amount,
            "non_compliant_pct": non_compliant_pct,
            "purification_amount": purification_amount,
            "purification_pct": purification_pct,
            "grade": grade,
            "grade_ar": grade_ar,
        },
        "recommendations": recommendations,
        "not_found": not_found,
    }

@app.get("/api/search")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query (ticker, Arabic or English name)")
):
    """Search stocks by ticker or name, with full Sharia verdict included."""
    stocks = load_stocks()
    query = q.strip().lower()

    results = []
    for s in stocks:
        if (
            q.strip() in s["ticker"]
            or query in s.get("name_en", "").lower()
            or q.strip() in s.get("name_ar", "")
        ):
            # Run full screen for each match
            result = screen_stock(s)
            results.append({
                "ticker": s["ticker"],
                "name_en": s["name_en"],
                "name_ar": s["name_ar"],
                "sector_en": s["sector_en"],
                "sector_ar": s["sector_ar"],
                "verdict": result.get("verdict", ""),
                "verdict_ar": result.get("verdict_ar", ""),
                "verdict_detail": result.get("verdict_detail", ""),
            })

    return results

@app.get("/api/stats")
async def market_stats():
    """Aggregate market statistics — total stocks, halal count, sectors."""
    stocks = load_stocks()
    total = len(stocks)

    verdict_counts = {"COMPLIANT": 0, "COMPLIANT_WITH_OVERLAY": 0, "COMPLIANT_WITH_PURIFICATION": 0, "NON_COMPLIANT": 0}
    sector_stats: dict[str, dict] = {}

    for s in stocks:
        result = screen_stock(s)
        verdict = result.get("verdict", "NON_COMPLIANT")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

        sector_key = s.get("sector_en", "Unknown")
        sector_ar = s.get("sector_ar", sector_key)

        if sector_key not in sector_stats:
            sector_stats[sector_key] = {
                "sector_en": sector_key,
                "sector_ar": sector_ar,
                "total": 0,
                "compliant": 0,
                "non_compliant": 0,
                "purification": 0,
            }

        sector_stats[sector_key]["total"] += 1
        if verdict == "COMPLIANT":
            sector_stats[sector_key]["compliant"] += 1
        elif verdict in ("COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
            sector_stats[sector_key]["compliant"] += 1
            sector_stats[sector_key]["purification"] += 1
        else:
            sector_stats[sector_key]["non_compliant"] += 1

    halal_count = verdict_counts["COMPLIANT"] + verdict_counts["COMPLIANT_WITH_OVERLAY"] + verdict_counts["COMPLIANT_WITH_PURIFICATION"]

    sectors = []
    for sector_data in sorted(sector_stats.values(), key=lambda x: x["compliant"], reverse=True):
        total_s = sector_data["total"]
        sectors.append({
            **sector_data,
            "compliance_rate": round(sector_data["compliant"] / total_s * 100, 1) if total_s > 0 else 0,
        })

    return {
        "total_stocks": total,
        "halal_count": halal_count,
        "halal_pct": round(halal_count / total * 100, 1) if total > 0 else 0,
        "non_compliant_count": verdict_counts["NON_COMPLIANT"],
        "purification_count": verdict_counts["COMPLIANT_WITH_OVERLAY"] + verdict_counts["COMPLIANT_WITH_PURIFICATION"],
        "verdict_distribution": verdict_counts,
        "sectors": sectors,
        "standard": "AAOIFI Standard No. 21",
    }

@app.get("/api/market")
async def market_overview():
    """Comprehensive market dashboard data.

    Combines sector compliance heatmap, top halal stocks by market cap,
    compliance distribution, and key market metrics in a single call.
    Powers the Market Dashboard page.
    """
    stocks = load_stocks()
    total = len(stocks)

    # Screen all stocks and collect rich data
    all_screened = []
    sector_map: dict[str, dict] = {}
    verdict_counts = {"COMPLIANT": 0, "COMPLIANT_WITH_OVERLAY": 0, "COMPLIANT_WITH_PURIFICATION": 0, "NON_COMPLIANT": 0}

    for s in stocks:
        result = screen_stock(s)
        verdict = result.get("verdict", "NON_COMPLIANT")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        sector_key = s.get("sector_en", "Unknown")
        sector_ar = s.get("sector_ar", sector_key)

        is_halal = verdict in ("COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION")

        stock_entry = {
            "ticker": s["ticker"],
            "name_en": s["name_en"],
            "name_ar": s["name_ar"],
            "sector_en": sector_key,
            "sector_ar": sector_ar,
            "market_cap": s.get("market_cap", 0),
            "currency": s.get("currency", "SAR"),
            "verdict": verdict,
            "verdict_ar": result.get("verdict_ar", ""),
            "is_halal": is_halal,
            "debt_to_assets": result.get("debt_to_assets", 0),
            "non_compliant_income_ratio": result.get("non_compliant_income_ratio", 0),
        }
        all_screened.append(stock_entry)

        # Build sector heatmap
        if sector_key not in sector_map:
            sector_map[sector_key] = {
                "sector_en": sector_key,
                "sector_ar": sector_ar,
                "total": 0,
                "compliant": 0,
                "non_compliant": 0,
                "purification": 0,
                "total_market_cap": 0,
                "halal_market_cap": 0,
                "stocks": [],
            }

        sector_map[sector_key]["total"] += 1
        sector_map[sector_key]["total_market_cap"] += s.get("market_cap", 0)

        if is_halal:
            sector_map[sector_key]["compliant"] += 1
            sector_map[sector_key]["halal_market_cap"] += s.get("market_cap", 0)
            if verdict in ("COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
                sector_map[sector_key]["purification"] += 1
        else:
            sector_map[sector_key]["non_compliant"] += 1

    # Finalize sector data
    sectors = []
    for sd in sorted(sector_map.values(), key=lambda x: x["total_market_cap"], reverse=True):
        t = sd["total"]
        sectors.append({
            **sd,
            "compliance_rate": round(sd["compliant"] / t * 100, 1) if t > 0 else 0,
            "halal_market_share": round(sd["halal_market_cap"] / sd["total_market_cap"] * 100, 1) if sd["total_market_cap"] > 0 else 0,
        })

    halal_count = verdict_counts["COMPLIANT"] + verdict_counts["COMPLIANT_WITH_OVERLAY"] + verdict_counts["COMPLIANT_WITH_PURIFICATION"]

    # Top halal stocks by market cap
    top_halal = sorted(
        [s for s in all_screened if s["is_halal"]],
        key=lambda x: x["market_cap"],
        reverse=True
    )[:10]

    # Best ratio stocks (lowest debt-to-assets among halal)
    best_ratios = sorted(
        [s for s in all_screened if s["is_halal"] and s["debt_to_assets"] is not None],
        key=lambda x: x["debt_to_assets"]
    )[:5]

    total_market_cap = sum(s.get("market_cap", 0) for s in stocks)
    halal_market_cap = sum(s["market_cap"] for s in all_screened if s["is_halal"])

    return {
        "overview": {
            "total_stocks": total,
            "halal_count": halal_count,
            "halal_pct": round(halal_count / total * 100, 1) if total > 0 else 0,
            "non_compliant_count": verdict_counts["NON_COMPLIANT"],
            "purification_count": verdict_counts["COMPLIANT_WITH_OVERLAY"] + verdict_counts["COMPLIANT_WITH_PURIFICATION"],
            "total_market_cap": total_market_cap,
            "halal_market_cap": halal_market_cap,
            "halal_market_share_pct": round(halal_market_cap / total_market_cap * 100, 1) if total_market_cap > 0 else 0,
            "sectors_count": len(sector_map),
            "standard": "AAOIFI Standard No. 21",
        },
        "verdict_distribution": verdict_counts,
        "sectors": sectors,
        "best_ratio_stocks": best_ratios,
    }


@app.get("/api/sectors")
async def list_sectors():
    """List all unique sectors with Arabic + English names.

    Used by the Advanced Screener to populate the sector dropdown.
    """
    stocks = load_stocks()
    seen = {}
    for s in stocks:
        key = s.get("sector_en", "Unknown")
        if key not in seen:
            seen[key] = {
                "sector_en": key,
                "sector_ar": s.get("sector_ar", key),
                "count": 0,
            }
        seen[key]["count"] += 1
    return sorted(seen.values(), key=lambda x: x["sector_en"])


@app.get("/api/screen")
async def screen_stocks(
    compliance: Optional[str] = Query(None, description="Filter: compliant, purification, non_compliant"),
    sector: Optional[str] = Query(None, description="Filter by sector (English name)"),
    max_debt_ratio: Optional[float] = Query(None, ge=0, le=100, description="Max debt-to-assets ratio (%)"),
    max_non_compliant_income: Optional[float] = Query(None, ge=0, le=100, description="Max non-compliant income ratio (%)"),
    min_market_cap: Optional[float] = Query(None, ge=0, description="Minimum market cap"),
    sort_by: Optional[str] = Query("ticker", description="Sort: ticker, name, market_cap, debt_ratio"),
    sort_order: Optional[str] = Query("asc", description="asc or desc"),
):
    """Advanced stock screener with multiple filters and sorting."""
    stocks = load_stocks()
    results = []

    for s in stocks:
        result = screen_stock(s)
        verdict = result.get("verdict", "NON_COMPLIANT")

        # ── Compliance filter ──
        if compliance:
            if compliance == "compliant":
                if verdict not in ("COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
                    continue
            elif compliance == "non_compliant":
                if verdict != "NON_COMPLIANT":
                    continue
            elif compliance == "purification":
                if verdict not in ("COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
                    continue

        # ── Sector filter ──
        if sector:
            if s.get("sector_en", "") != sector:
                continue

        # ── Debt ratio filter ──
        debt_ratio = result.get("debt_to_assets")
        if debt_ratio is not None and max_debt_ratio is not None:
            if debt_ratio * 100 > max_debt_ratio:
                continue

        # ── Non-compliant income filter ──
        nc_ratio = result.get("non_compliant_income_ratio")
        if nc_ratio is not None and max_non_compliant_income is not None:
            if nc_ratio * 100 > max_non_compliant_income:
                continue

        # ── Market cap filter ──
        market_cap = s.get("market_cap", 0)
        if min_market_cap is not None and market_cap < min_market_cap:
            continue

        is_halal = verdict in ("COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION")

        results.append({
            "ticker": s["ticker"],
            "name_en": s["name_en"],
            "name_ar": s["name_ar"],
            "sector_en": s.get("sector_en", ""),
            "sector_ar": s.get("sector_ar", ""),
            "market_cap": market_cap,
            "currency": s.get("currency", "SAR"),
            "verdict": verdict,
            "verdict_ar": result.get("verdict_ar", ""),
            "is_halal": is_halal,
            "ratios": {
                "debt_to_assets": result.get("debt_to_assets"),
                "debt_to_market_cap": result.get("debt_to_market_cap"),
                "interest_investments_ratio": result.get("interest_investments_ratio"),
                "receivables_ratio": result.get("receivables_ratio"),
                "non_compliant_income_ratio": result.get("non_compliant_income_ratio"),
                "illiquid_assets_ratio": result.get("illiquid_assets_ratio"),
            },
            "total_assets": s.get("total_assets", 0),
            "total_revenue": s.get("total_revenue", 0),
        })

    # ── Sorting ──
    reverse = sort_order == "desc"
    sort_key_map = {
        "ticker": "ticker",
        "name": "name_en",
        "market_cap": "market_cap",
        "debt_ratio": "_debt_sort",
    }
    key = sort_key_map.get(sort_by, "ticker")

    if key == "_debt_sort":
        results.sort(key=lambda x: x["ratios"]["debt_to_assets"] if x["ratios"]["debt_to_assets"] is not None else 999, reverse=reverse)
    else:
        results.sort(key=lambda x: x.get(key, ""), reverse=reverse)

    return {
        "count": len(results),
        "total_universe": len(stocks),
        "stocks": results,
    }

# ════════════════════════════════════════════════════════════════════════════
# PRICE HISTORY ENDPOINT
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/stocks/{ticker}/history")
async def get_stock_history(
    ticker: str,
    range: str = Query("1mo", pattern="^(1mo|3mo|6mo|1y)$"),
):
    """Get historical price data for a stock.

    Returns daily or weekly close prices from Yahoo Finance.
    Ranges: 1mo (daily), 3mo (daily), 6mo (weekly), 1y (weekly).
    Fails soft: returns 404 if no data available.
    """
    try:
        prices = get_price_history(ticker, range)
    except Exception as e:
        logger.warning(f"Price history error for {ticker}: {e}")
        prices = None

    if not prices:
        raise HTTPException(
            status_code=404,
            detail="Price history not available for this ticker.",
        )

    return {
        "ticker": ticker,
        "range": range,
        "prices": prices,
        "source": "Yahoo Finance",
    }


# ════════════════════════════════════════════════════════════════════════════
# PORTFOLIO DIVERSIFICATION ENDPOINT (requires auth)
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/portfolio/diversification")
def portfolio_diversification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sector allocation breakdown for the user's portfolio.

    Computes market value per holding using live prices, groups by sector,
    and returns weight percentages with a concentration risk assessment.
    """
    holdings = db.query(Holding).filter(
        Holding.user_id == current_user.id,
    ).all()

    if not holdings:
        return {
            "sectors": [],
            "total_value": 0,
            "top_sector_weight": 0,
            "concentration_risk": "DIVERSIFIED",
            "sector_count": 0,
        }

    # Get live prices for all holdings
    tickers = list({h.ticker for h in holdings})
    prices = get_prices_bulk(tickers)

    # Build a lookup from stocks.json for sector info
    stock_map = {s["ticker"]: s for s in load_stocks()}

    # Compute market value per holding and group by sector
    sector_data: dict[str, dict] = {}  # sector_en -> {market_value, holding_count, sector_ar}

    for h in holdings:
        live = prices.get(h.ticker)
        if not live or live.get("price") is None:
            continue

        market_value = h.quantity * live["price"]

        # Get sector info: prefer holding's stored sector, fall back to stocks.json
        stock_info = stock_map.get(h.ticker, {})
        sector_en = h.sector_en or stock_info.get("sector_en") or "Unknown"
        sector_ar = h.sector_ar or stock_info.get("sector_ar") or "غير محدد"

        if sector_en not in sector_data:
            sector_data[sector_en] = {
                "sector_en": sector_en,
                "sector_ar": sector_ar,
                "market_value": 0.0,
                "holding_count": 0,
            }
        sector_data[sector_en]["market_value"] += market_value
        sector_data[sector_en]["holding_count"] += 1

    total_value = sum(s["market_value"] for s in sector_data.values())

    if total_value == 0:
        return {
            "sectors": [],
            "total_value": 0,
            "top_sector_weight": 0,
            "concentration_risk": "DIVERSIFIED",
            "sector_count": 0,
        }

    # Compute weight percentages and sort by market value descending
    sectors = []
    for s in sector_data.values():
        s["market_value"] = round(s["market_value"], 2)
        s["weight_pct"] = round(s["market_value"] / total_value * 100, 2)
        sectors.append(s)
    sectors.sort(key=lambda x: x["market_value"], reverse=True)

    top_sector_weight = sectors[0]["weight_pct"] if sectors else 0

    if top_sector_weight > 50:
        concentration_risk = "HIGH"
    elif top_sector_weight > 30:
        concentration_risk = "MODERATE"
    else:
        concentration_risk = "DIVERSIFIED"

    return {
        "sectors": sectors,
        "total_value": round(total_value, 2),
        "top_sector_weight": top_sector_weight,
        "concentration_risk": concentration_risk,
        "sector_count": len(sectors),
    }


# ════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION GUARD
# ════════════════════════════════════════════════════════════════════════════

def require_subscription(user: User = Depends(get_current_user)) -> User:
    """Dependency: raises 402 if user is not subscribed."""
    info = stripe_service.get_subscription_info(user)
    if not info["is_subscribed"]:
        raise HTTPException(
            status_code=402,
            detail="Subscription required to generate research reports",
        )
    return user


# ════════════════════════════════════════════════════════════════════════════
# RESEARCH ENGINE ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/research", response_model=ResearchJobResponse, status_code=201)
@limiter.limit("5/hour")
def start_research(
    request: Request,
    req: ResearchRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_subscription),
    db: Session = Depends(get_db),
):
    """Start an AI investment research report for a given ticker.

    Requires active subscription. Returns immediately with a job_id;
    the report is generated asynchronously (typically 60-120 seconds).
    """
    ticker = req.ticker.strip().upper()

    # Rate limit: max 5 reports/day
    if not research_engine.check_daily_rate_limit(user.id, db):
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached ({research_engine.DAILY_REPORT_LIMIT} reports/day). Try again tomorrow.",
        )

    # Check if a report for this ticker already exists in last 24h
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    existing = (
        db.query(ResearchReport)
        .filter(
            ResearchReport.user_id == user.id,
            ResearchReport.ticker == ticker,
            ResearchReport.created_at >= cutoff,
            ResearchReport.is_sample == False,
        )
        .order_by(ResearchReport.created_at.desc())
        .first()
    )
    if existing:
        return ResearchJobResponse(
            job_id=existing.id, ticker=ticker, status=existing.status
        )

    # Create a pending report
    report = ResearchReport(
        user_id=user.id,
        ticker=ticker,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Schedule background generation
    background_tasks.add_task(research_engine.generate_research_report, report.id)

    return ResearchJobResponse(job_id=report.id, ticker=ticker, status="pending")


# ── SSE streaming endpoint — agent pipeline progress ──────────────────────


@app.get("/api/reports/{report_id}/stream")
async def stream_report_progress(
    report_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE endpoint that streams agent pipeline progress for a research report.

    The client connects after starting a research job. The server sends
    ``progress`` events as each agent node starts/completes, and a final
    ``complete`` event when the pipeline finishes.

    Usage (frontend):
        const source = new EventSource(`/api/reports/${jobId}/stream`);
        source.onmessage = (e) => {
            const data = JSON.parse(e.data);
            // data.agents: array of agent steps
            // data.status: "running" | "complete"
        };
    """
    from agent_pipeline.progress import get_tracker

    async def event_generator():
        tracker = get_tracker()
        last_len = 0

        while True:
            agents = tracker.get_progress(report_id)
            is_complete = tracker.is_complete(report_id)
            current_len = len(agents)

            # Only send if new info is available
            if current_len != last_len or (is_complete and current_len > 0):
                last_len = current_len
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": "complete" if is_complete else "running",
                        "agents": agents,
                    }),
                }

            if is_complete:
                break

            await asyncio.sleep(1)

        yield {
            "event": "complete",
            "data": json.dumps({"status": "complete"}),
        }

    return EventSourceResponse(event_generator())






@app.get("/api/research/history", response_model=list[ResearchListItem])
def research_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the user's past research reports (no markdown content)."""
    reports = (
        db.query(ResearchReport)
        .filter(
            ResearchReport.user_id == user.id,
            ResearchReport.is_sample == False,
        )
        .order_by(ResearchReport.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ResearchListItem.model_validate(r) for r in reports]

@app.get("/api/research/samples", response_model=list[ResearchReportResponse])
def research_samples(db: Session = Depends(get_db)):
    """Get public demo research reports. No auth required.

    These are full-quality reports that showcase the product.
    """
    reports = (
        db.query(ResearchReport)
        .filter(ResearchReport.is_sample == True)
        .order_by(ResearchReport.created_at.desc())
        .all()
    )
    return [ResearchReportResponse.model_validate(r) for r in reports]

@app.get("/api/research/{job_id}", response_model=ResearchReportResponse)
def get_research(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the status and content of a research report.

    Poll this endpoint after starting a research job. Status transitions:
    pending → running → completed | failed
    """
    report = db.query(ResearchReport).filter(ResearchReport.id == job_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Research report not found")

    # Ownership check (sample reports are viewable by everyone)
    if not report.is_sample and report.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return ResearchReportResponse.model_validate(report)

# ════════════════════════════════════════════════════════════════════════════
# BILLING ENDPOINTS (Stripe)
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/billing/subscription", response_model=SubscriptionResponse)
def get_subscription(
    user: User = Depends(get_current_user),
):
    """Check the current user's subscription status."""
    info = stripe_service.get_subscription_info(user)
    return SubscriptionResponse(**info)


@app.post("/api/billing/create-checkout-session", response_model=CheckoutResponse)
def create_checkout(
    req: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for subscription."""
    url = stripe_service.create_checkout_session(user, req.plan)
    db.commit()  # commit any customer_id changes
    return CheckoutResponse(url=url)


@app.post("/api/billing/create-portal-session", response_model=PortalResponse)
def create_portal(
    user: User = Depends(get_current_user),
):
    """Create a Stripe Customer Portal session for subscription management."""
    url = stripe_service.create_portal_session(user)
    return PortalResponse(url=url)


@app.post("/api/billing/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Stripe webhook receiver. Verifies signature and processes events."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    success = stripe_service.process_webhook_event(payload, signature, db)
    if not success:
        raise HTTPException(status_code=400, detail="Webhook verification failed")
    return {"received": True}




# ── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    # reload=True only for local dev; production uses gunicorn (see Dockerfile)
    is_dev = os.getenv("APP_ENV", "development") != "production"
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=is_dev)