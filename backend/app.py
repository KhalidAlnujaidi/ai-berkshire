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
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Import the Sharia screener ──────────────────────────────────────────────
# The screener lives in the parent directory (tools/sharia_screener.py)
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from sharia_screener import screen_company, screen_sector  # noqa: E402

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


# ── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mizan API",
    description="Sharia-compliant investment screening API for Saudi Arabia",
    version="1.2.0",
)

# CORS — allow the Vercel frontend and localhost dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://mizan-invest.com",
        "https://www.mizan-invest.com",
        "https://mizan-invest.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ─────────────────────────────────────────────────────────

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


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    stocks = load_stocks()
    return {
        "status": "ok",
        "service": "Mizan Sharia Screening API",
        "version": "1.1.0",
        "standard": "AAOIFI Standard No. 21",
        "stocks_count": len(stocks),
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
                "is_halal": result.get("verdict", "") in (
                    "COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"
                ),
            })

    return results


# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
