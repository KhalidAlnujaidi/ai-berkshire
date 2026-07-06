"""Data-fetching tools for the Mizan agent pipeline.

Each function returns a formatted string suitable for injection into an
LLM prompt.  They wrap Mizan's existing data modules (stock_data.py,
sharia_screener.py) — no new external dependencies.

These are NOT LangChain tools (no @tool decorator, no bind_tools). The
graph pre-fetches all data before the first analyst runs and injects it
into the state, following the sentiment-analyst pattern from
TradingAgents. This avoids tool-calling loops and is more reliable.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sharia_screener import screen_ratios, screen_sector
from stock_data import get_price, get_price_history

logger = logging.getLogger(__name__)


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
    """Fetch fundamental data. Mizan doesn't have a dedicated fundamentals API,
    so we use price-derived metrics from Yahoo Finance.

    In Phase 2 this can be upgraded to use yfinance's .info/.financials.
    """
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
        "\n**Note**: Detailed balance sheet / income statement data is not yet "
        "integrated. The analyst should focus on price action, sector context, "
        "and qualitative factors."
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# News data
# ---------------------------------------------------------------------------


def fetch_news_data(ticker: str) -> str:
    """Fetch recent news. Phase 1 uses Yahoo Finance headlines via stock_data.

    Phase 2 will add Argaam, Mubasher, Saudi Gazette for Saudi-specific news.
    """
    lines = ["## News & Market Context"]

    # Use price data for basic market context
    price_data = get_price(ticker)
    if price_data:
        lines.append(f"- Exchange: {price_data.get('exchange', 'N/A')}")
        lines.append(f"- Currency: {price_data.get('currency', 'N/A')}")
        lines.append(f"- Market State: {price_data.get('market_state', 'N/A')}")

    today = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"\n- Analysis Date: {today}")
    lines.append(
        "\n**Note**: Automated news fetching (Argaam, Mubasher) is not yet "
        "integrated in Phase 1. The news analyst should provide macro context "
        "based on available market data and sector knowledge."
    )

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
        for ratio_name, ratio_data in ratio_result.get("ratios", {}).items():
            status = "✅" if ratio_data.get("passed") else "❌"
            lines.append(f"- {ratio_name}: {ratio_data.get('value', 'N/A')}% {status} (limit: {ratio_data.get('threshold', 'N/A')}%)")
        lines.append(f"\n- Overall Quantitative Pass: {'✅' if ratio_result.get('compliant') else '❌'}")
        if not ratio_result.get("compliant"):
            lines.append(f"- Failed Ratios: {', '.join(ratio_result.get('failed_ratios', []))}")
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
    elif has_financials and not ratio_result.get("compliant"):
        is_compliant = False
        verdict = "NON-COMPLIANT"
    elif sector_result and sector_result["category"] == "permitted_with_overlay":
        verdict = "COMPLIANT WITH PURIFICATION"
    else:
        verdict = "COMPLIANT"

    lines.append(f"\n### Overall Sharia Verdict: {verdict}")

    return "\n".join(lines)
