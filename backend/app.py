"""Mizan Backend API — FastAPI application.

Wraps the sharia_screener.py engine as a REST API for the Mizan web app.
Provides:
  - GET  /api/health          — health check
  - GET  /api/stocks          — list all stocks in database
  - GET  /api/stocks/{ticker} — get single stock + Sharia verdict
  - POST /api/sharia-screen   — screen a company with custom financial data
  - GET  /api/search?q=...    — search stocks by name or ticker
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


# ── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mizan API",
    description="Sharia-compliant investment screening API for Saudi Arabia",
    version="1.0.0",
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
        "version": "1.0.0",
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


@app.get("/api/stocks/{ticker}")
async def get_stock(ticker: str):
    """Get a single stock with full Sharia compliance screening."""
    stock = find_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found")

    # Run the Sharia screen
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

    # Merge stock info with screening result
    return {
        **result,
        "name_ar": stock["name_ar"],
        "sector_ar": stock["sector_ar"],
    }


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


@app.get("/api/search")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query (ticker, Arabic or English name)")
):
    """Search stocks by ticker or name."""
    stocks = load_stocks()
    query = q.strip().lower()

    results = []
    for s in stocks:
        if (
            q.strip() in s["ticker"]
            or query in s.get("name_en", "").lower()
            or q.strip() in s.get("name_ar", "")
        ):
            # Include a quick sector screen
            sector_info = screen_sector(s["sector_en"])
            results.append({
                **StockBrief(
                    ticker=s["ticker"],
                    name_ar=s["name_ar"],
                    name_en=s["name_en"],
                    sector_ar=s["sector_ar"],
                    sector_en=s["sector_en"],
                ).model_dump(),
                "sharia_category": sector_info["category"],
            })

    return results


# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
