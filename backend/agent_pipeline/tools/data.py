"""Data-fetching tools for the Mizan agent pipeline.

Each function returns a formatted string suitable for injection into an
LLM prompt.  They wrap Mizan's existing data modules (stock_data.py,
sharia_screener.py) and yfinance for real fundamental data — no new
external dependencies.

These are NOT LangChain tools (no @tool decorator, no bind_tools). The
graph pre-fetches all data before the first analyst runs and injects it
into the state, following the sentiment-analyst pattern from
TradingAgents. This avoids tool-calling loops and is more reliable.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sharia_screener import screen_ratios, screen_sector
from stock_data import get_price, get_price_history

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fmt(value: float | None, decimals: int = 2) -> str:
    """Format a number nicely, returning 'N/A' if None."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def _fmt_bn(value: float | None) -> str:
    """Format a large number as billions with 2 decimal places."""
    if value is None:
        return "N/A"
    return f"{value / 1e9:,.2f}B"


def _fmt_pct(value: float | None) -> str:
    """Format a ratio as a percentage string."""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%" if value < 1 else f"{value:.1f}%"


# ---------------------------------------------------------------------------
# yfinance fundamentals — fetches everything in one Ticker call
# ---------------------------------------------------------------------------


_YFINANCE_LOADED = False
try:
    import yfinance as yf
    _YFINANCE_LOADED = hasattr(yf, "Ticker")
except ImportError:
    pass


def fetch_yfinance_financials(ticker: str) -> dict[str, Any]:
    """Fetch real financial data from yfinance.

    Returns a dict with:
      - formatted_str: a nicely formatted section for the fundamentals report
      - raw: a dict of raw numbers for Sharia screening (pass to **kwargs)
      - sector: the GICS sector string
      - company_name: the human-readable company name

    On failure, returns a dict with empty/fallback values instead of
    crashing — the pipeline degrades gracefully.
    """
    result: dict[str, Any] = {
        "formatted_str": "",
        "raw": {},
        "sector": "",
        "company_name": "",
    }

    if not _YFINANCE_LOADED:
        logger.warning("yfinance not available — fundamental data will be limited")
        return result

    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
    except Exception:
        logger.warning(f"yfinance: failed to load Ticker({ticker})", exc_info=True)
        return result

    # ── Company identity ──────────────────────────────────────────────
    result["company_name"] = info.get("longName") or info.get("shortName") or ""
    result["sector"] = info.get("sector") or ""
    industry = info.get("industry") or ""

    # ── Balance-sheet derived ratios ──────────────────────────────────
    # yfinance.info has most of what we need; fall back to balance_sheet if missing
    total_assets: float | None = info.get("totalAssets")
    total_debt: float | None = info.get("totalDebt", info.get("totalDebt"))
    market_cap: float | None = info.get("marketCap")
    total_revenue: float | None = info.get("totalRevenue")
    net_income: float | None = info.get("netIncomeToCommon")

    # Cash & equivalents — try balance sheet if not in info
    cash: float | None = info.get("cashAndShortTermInvestments")
    if cash is None:
        try:
            bs = stock.balance_sheet
            if bs is not None and bs.shape[1] > 0:
                row = bs.iloc[:, 0]
                cash = float(row.get("Cash Cash Equivalents And Short Term Investments", 0))
                # Only overwrite total_assets if info didn't have it
                if total_assets is None:
                    total_assets = float(row.get("Total Assets", 0))
                if total_debt is None:
                    total_debt = float(row.get("Total Debt", 0))
        except Exception:
            pass

    # Accounts receivable
    receivables: float | None = None
    try:
        bs = stock.balance_sheet
        if bs is not None and bs.shape[1] > 0:
            row = bs.iloc[:, 0]
            receivables = float(row.get("Accounts Receivable", 0))
    except Exception:
        pass

    # Interest-bearing investments = financial assets (short-term investments)
    ibi = info.get("shortTermInvestments")

    # Non-compliant income — not available from yfinance; default to 0
    non_compliant_income = 0.0

    # ── Build raw dict for Sharia screening ───────────────────────────
    raw: dict[str, float] = {}
    if total_assets is not None:
        raw["total_assets"] = total_assets
    if total_debt is not None:
        raw["total_debt"] = total_debt
    if cash is not None:
        raw["cash_and_equivalents"] = cash
    if receivables is not None:
        raw["accounts_receivable"] = receivables
    if market_cap is not None:
        raw["market_cap"] = market_cap
    if ibi is not None:
        raw["interest_bearing_investments"] = ibi
    if total_revenue is not None:
        raw["total_revenue"] = total_revenue
    raw["non_compliant_income"] = non_compliant_income

    result["raw"] = raw

    # ── Build formatted string ────────────────────────────────────────
    lines = ["## Fundamental Data"]
    lines.append(f"### Company")
    lines.append(f"- Company: {result['company_name'] or result.get('sector', ticker)}")
    lines.append(f"- Ticker: {ticker}")
    if result["sector"]:
        lines.append(f"- Sector: {result['sector']}")
    if industry:
        lines.append(f"- Industry: {industry}")

    lines.append("")
    lines.append("### Valuation")
    price_data = get_price(ticker)
    if price_data and price_data.get("price"):
        lines.append(f"- Current Price: {price_data['price']} {price_data.get('currency', '')}")
        if market_cap:
            lines.append(f"- Market Cap: {_fmt_bn(market_cap)}")
        pe = info.get("trailingPE")
        if pe:
            lines.append(f"- Trailing P/E: {pe:.2f}")
        fpe = info.get("forwardPE")
        if fpe:
            lines.append(f"- Forward P/E: {fpe:.2f}")
        pb = info.get("priceToBook")
        if pb:
            lines.append(f"- Price/Book: {pb:.2f}")
        dy = info.get("dividendYield")
        if dy:
            lines.append(f"- Dividend Yield: {_fmt_pct(dy)}")
        target = info.get("targetMeanPrice")
        if target:
            lines.append(f"- Analyst Target: {target:.2f} ({info.get('currency', '')})")
        rec = info.get("recommendationKey")
        if rec:
            lines.append(f"- Analyst Consensus: {rec.upper()}")

    lines.append("")
    lines.append("### Financial Health")
    if total_debt is not None:
        lines.append(f"- Total Debt: {_fmt_bn(total_debt)}")
    if total_assets is not None and total_debt is not None and total_assets > 0:
        dtoa = (total_debt / total_assets) * 100
        lines.append(f"- Debt/Assets: {dtoa:.1f}%")
    if cash is not None:
        lines.append(f"- Cash & Equivalents: {_fmt_bn(cash)}")
    if receivables is not None:
        lines.append(f"- Accounts Receivable: {_fmt_bn(receivables)}")
    qr = info.get("quickRatio")
    if qr:
        lines.append(f"- Quick Ratio: {qr:.2f}")
    cr = info.get("currentRatio")
    if cr:
        lines.append(f"- Current Ratio: {cr:.2f}")
    dte = info.get("debtToEquity")
    if dte:
        lines.append(f"- Debt/Equity: {dte:.1f}%")

    lines.append("")
    lines.append("### Profitability")
    if total_revenue is not None:
        lines.append(f"- Total Revenue (TTM): {_fmt_bn(total_revenue)}")
    if net_income is not None:
        lines.append(f"- Net Income (TTM): {_fmt_bn(net_income)}")
    pm = info.get("profitMargins")
    if pm:
        lines.append(f"- Profit Margin: {_fmt_pct(pm)}")
    roe = info.get("returnOnEquity")
    if roe:
        lines.append(f"- Return on Equity: {_fmt_pct(roe)}")
    roa = info.get("returnOnAssets")
    if roa:
        lines.append(f"- Return on Assets: {_fmt_pct(roa)}")
    rg = info.get("revenueGrowth")
    if rg:
        lines.append(f"- Revenue Growth (YoY): {_fmt_pct(rg)}")
    eg = info.get("earningsGrowth")
    if eg:
        lines.append(f"- Earnings Growth (YoY): {_fmt_pct(eg)}")

    # Business summary — for context
    summary = info.get("longBusinessSummary", "")
    if summary:
        # Truncate to keep prompt size manageable
        short_summary = summary[:600] + "..." if len(summary) > 600 else summary
        lines.append("")
        lines.append("### Business Profile")
        lines.append(short_summary)

    result["formatted_str"] = "\n".join(lines)
    return result


# ---------------------------------------------------------------------------
# Market / price data
# ---------------------------------------------------------------------------


def fetch_market_data(ticker: str) -> str:
    """Fetch current price + 6-month history and format as a context string."""
    lines = []
    price_data = get_price(ticker)

    if price_data:
        lines.append("## Current Market Data")
        lines.append(f"- Current Price: {price_data.get('price', 'N/A')} {price_data.get('currency', '')}")
        lines.append(f"- Previous Close: {price_data.get('previous_close', 'N/A')}")
        if price_data.get('day_change_pct') is not None:
            lines.append(f"- Day Change: {price_data.get('day_change_pct')}%")
        lines.append(
            f"- 52-Week Range: {price_data.get('fifty_two_week_low', 'N/A')} - "
            f"{price_data.get('fifty_two_week_high', 'N/A')}"
        )
        lines.append(f"- Exchange: {price_data.get('exchange', 'N/A')}")
        lines.append(f"- Market State: {price_data.get('market_state', 'N/A')}")
        if price_data.get('volume'):
            lines.append(f"- Volume: {price_data.get('volume'):,}")
    else:
        lines.append("## Market Data\n- [No live price data available for this ticker]")

    # Historical data for trend analysis
    history = get_price_history(ticker, "6mo")
    if history and len(history) > 1:
        lines.append("\n## 6-Month Price History (weekly)")
        lines.append("| Date | Close | Volume |")
        lines.append("|------|-------|--------|")
        # Sample every ~2nd point to keep prompt size manageable
        step = max(1, len(history) // 15)
        for bar in history[::step]:
            vol_str = f"{bar['volume']:,}" if bar.get('volume') else "—"
            lines.append(f"| {bar['date']} | {bar['close']:.2f} | {vol_str} |")

        # Simple trend stats
        closes = [b['close'] for b in history]
        if len(closes) >= 2:
            pct_change = ((closes[-1] - closes[0]) / closes[0]) * 100
            high = max(closes)
            low = min(closes)
            lines.append(f"\n- 6-Month Change: {pct_change:+.1f}%")
            lines.append(f"- 6-Month High: {high:.2f}")
            lines.append(f"- 6-Month Low: {low:.2f}")
    else:
        lines.append("\n[No historical price data available]")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fundamentals data
# ---------------------------------------------------------------------------


def fetch_fundamentals_data(ticker: str) -> str:
    """Fetch real fundamental data via yfinance and format as an LLM context string.

    Covers valuation, financial health, and profitability metrics.
    Falls back gracefully if yfinance is unavailable.
    """
    fin = fetch_yfinance_financials(ticker)
    if fin.get("formatted_str"):
        return fin["formatted_str"]

    # Fallback: price-derived data only
    lines = ["## Fundamental Data"]
    price_data = get_price(ticker)
    if price_data:
        lines.append(f"- Market Price: {price_data.get('price', 'N/A')} {price_data.get('currency', '')}")
        if price_data.get('fifty_two_week_low') and price_data.get('fifty_two_week_high'):
            low = price_data['fifty_two_week_low']
            high = price_data['fifty_two_week_high']
            mid = (low + high) / 2
            lines.append(f"- 52-Week Midpoint: {mid:.2f}")
            if price_data.get('price'):
                pos = ((price_data['price'] - low) / (high - low)) * 100 if high > low else 50
                lines.append(f"- Current position in 52-Week Range: {pos:.0f}%")
    else:
        lines.append("- [No fundamental data available — limited price data]")

    lines.append(
        "\n**Note**: Detailed balance sheet / income statement data was not "
        "retrievable for this ticker. The analyst should focus on price action, "
        "sector context, and qualitative factors."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# News data
# ---------------------------------------------------------------------------


def fetch_news_data(ticker: str) -> str:
    """Fetch recent news headlines using yfinance.

    Falls back to market context summary if yfinance is unavailable or
    returns no news (common for non-US tickers).
    """
    lines = ["## News & Market Context"]

    # ── Try yfinance news ─────────────────────────────────────────────
    news_headlines: list[str] = []
    if _YFINANCE_LOADED:
        try:
            stock = yf.Ticker(ticker)
            raw_news = stock.news or []
            for item in raw_news[:8]:  # max 8 headlines
                title = (item.get("title") or "").strip()
                if title and title != "N/A":
                    publisher = (item.get("publisher") or "").strip()
                    if publisher and publisher != "N/A":
                        news_headlines.append(f"- {title} ({publisher})")
                    else:
                        news_headlines.append(f"- {title}")
        except Exception:
            logger.debug(f"yfinance news fetch failed for {ticker}", exc_info=True)

    # ── Market context from price data ────────────────────────────────
    price_data = get_price(ticker)
    if price_data:
        lines.append(f"- Exchange: {price_data.get('exchange', 'N/A')}")
        lines.append(f"- Currency: {price_data.get('currency', 'N/A')}")
        lines.append(f"- Market State: {price_data.get('market_state', 'N/A')}")
        if price_data.get("name"):
            lines.append(f"- Company: {price_data['name']}")

    today = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"\n- Analysis Date: {today}")

    if news_headlines:
        lines.append("\n### Recent Headlines")
        lines.extend(news_headlines)
        lines.append(
            "\n*Note: News from Yahoo Finance. For Saudi-specific news, consider "
            "supplementing with Argaam (argaam.com) or Mubasher (mubasher.info).*"
        )
    else:
        lines.append(
            "\n*No recent headlines available for this ticker from Yahoo Finance. "
            "The news analyst should provide macro context based on available market "
            "data and sector knowledge.*"
        )

    # ── Analyst sentiment ─────────────────────────────────────────────
    if _YFINANCE_LOADED:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            rec = info.get("recommendationKey")
            target = info.get("targetMeanPrice")
            n_analysts = info.get("numberOfAnalystOpinions")
            if rec or target:
                lines.append("\n### Analyst Sentiment")
                if rec:
                    lines.append(f"- Consensus: {rec.upper()}")
                if target:
                    lines.append(f"- Mean Target: {target:.2f} {price_data.get('currency', '') if price_data else ''}")
                if n_analysts:
                    lines.append(f"- Analysts Covering: {n_analysts}")
        except Exception:
            pass

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sharia compliance data
# ---------------------------------------------------------------------------


def fetch_sharia_data(
    ticker: str,
    sector: str = "",
    total_assets: float = 0,
    total_debt: float = 0,
    interest_bearing_investments: float = 0,
    accounts_receivable: float = 0,
    cash_and_equivalents: float = 0,
    market_cap: float = 0,
    non_compliant_income: float = 0,
    total_revenue: float = 0,
) -> str:
    """Run deterministic Sharia compliance screening and format results.

    Wraps sharia_screener.py which implements AAOIFI Standard No. 21.
    If financial data is not provided (all zeros), only the qualitative
    (sector) screen runs.
    """
    lines = ["## Sharia Compliance Screening (AAOIFI Standard No. 21)"]

    # Qualitative screen — always runs
    sector_result = screen_sector(sector) if sector else None
    if sector_result:
        lines.append("\n### Qualitative Screen (Business Activity)")
        lines.append(f"- Sector: {sector}")
        lines.append(f"- Category: {sector_result['category']}")
        lines.append(f"- Compliant: {'✅' if sector_result['compliant'] else '❌'}")
        lines.append(f"- Notes: {sector_result['notes']}")

        if not sector_result["compliant"]:
            lines.append("\n**⚠️ HARD FAIL: Non-compliant sector. Stock cannot be held by Sharia funds.**")
    else:
        lines.append("\n### Qualitative Screen\n- Sector not provided; qualitative screen skipped.")

    # Quantitative screen — only if data is available
    has_financials = any([
        total_assets, total_debt, interest_bearing_investments,
        accounts_receivable, cash_and_equivalents,
    ])
    if has_financials and total_assets > 0:
        ratio_result = screen_ratios(
            total_assets=total_assets,
            total_debt=total_debt,
            interest_bearing_investments=interest_bearing_investments,
            accounts_receivable=accounts_receivable,
            cash_and_equivalents=cash_and_equivalents,
            market_cap=market_cap,
            non_compliant_income=non_compliant_income,
            total_revenue=total_revenue,
        )

        lines.append("\n### Quantitative Screen (Financial Ratios)")
        lines.append("| Ratio | Value | Threshold | Status |")
        lines.append("|-------|-------|-----------|--------|")
        for ratio_name, ratio_data in ratio_result.items():
            if ratio_name.startswith("_"):
                continue
            if isinstance(ratio_data, dict) and "value" in ratio_data:
                status = "✅ PASS" if ratio_data.get("passed") else "❌ FAIL"
                val = ratio_data.get("value", "N/A")
                thresh = ratio_data.get("threshold", "N/A")
                label = ratio_data.get("label", ratio_name)
                if isinstance(val, float):
                    val_str = f"{val:.2f}%"
                else:
                    val_str = str(val)
                if isinstance(thresh, float):
                    thresh_str = f"{thresh:.2f}%"
                else:
                    thresh_str = str(thresh)
                lines.append(f"| {label} | {val_str} | {thresh_str} | {status} |")

        overall = ratio_result.get("_overall_quantitative")
        if overall is not None:
            status = "✅ PASS" if overall else "❌ FAIL"
            lines.append(f"\n**Quantitative Overall: {status}**")
    else:
        lines.append(
            "\n### Quantitative Screen\n- Detailed financial data not available. "
            "Ratio screen skipped. Analyst should note this limitation."
        )

    # Summary verdict
    is_compliant = True
    if sector_result and not sector_result["compliant"]:
        is_compliant = False
        verdict = "NON-COMPLIANT"
    elif has_financials and total_assets > 0 and not ratio_result.get("_overall_quantitative"):
        is_compliant = False
        verdict = "NON-COMPLIANT"
    elif sector_result and sector_result["category"] == "permitted_with_overlay":
        verdict = "COMPLIANT WITH PURIFICATION"
    else:
        verdict = "COMPLIANT"

    lines.append(f"\n### Overall Sharia Verdict: {verdict}")

    return "\n".join(lines)
