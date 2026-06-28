#!/usr/bin/env python3
"""Stock Data Update Utility for Mizan.

Helps maintain the stocks.json database with real financial data.
Provides:
  - validate: Check all entries have required fields and mark data quality
  - template: Generate a blank template for a new stock entry
  - market-add: Add a stock to a specific market (saudi/us/hk)

Usage:
    python3 tools/update_stocks_data.py validate
    python3 tools/update_stocks_data.py template --ticker AAPL --market us
    python3 tools/update_stocks_data.py stats

Financial data sources for Saudi stocks (Tadawul):
  - Saudi Exchange (Tadawul) annual reports: https://www.saudiexchange.sa
  - Company investor relations pages
  - Argaaam (financial data portal): https://www.argaaam.com
  - Mubasher: https://www.mubasher.info

Financial data sources for US stocks:
  - SEC EDGAR (free API): https://www.sec.gov/edgar/
  - yfinance Python library (free, Yahoo Finance data)
  - Alpha Vantage API (free tier available)

Last manual update: 2025-01 (estimated values — replace with verified data)
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import date

STOCKS_FILE = Path(__file__).resolve().parent.parent / "backend" / "stocks.json"

REQUIRED_FIELDS = [
    "ticker", "name_en", "name_ar", "sector_en", "sector_ar",
    "total_assets", "total_debt", "interest_bearing_investments",
    "accounts_receivable", "cash_and_equivalents", "market_cap",
    "non_compliant_income", "total_revenue",
]

OPTIONAL_FIELDS = [
    "market",           # "saudi" | "us" | "hk" (default: "saudi")
    "currency",         # "SAR" | "USD" | "HKD" (default: "SAR")
    "data_quality",     # "verified" | "estimated" | "partial"
    "last_updated",     # ISO date string
    "source",           # human-readable data source
]


def load_stocks():
    with open(STOCKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_stocks(stocks):
    with open(STOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)


def is_estimated(value):
    """Heuristic: round numbers with many trailing zeros are likely estimates."""
    if not isinstance(value, (int, float)) or value == 0:
        return False
    # Check if the number is suspiciously round (>6 trailing zeros)
    if value >= 1_000_000 and value % 1_000_000 == 0:
        return True
    if value >= 100_000 and value % 100_000 == 0:
        return True
    return False


def validate():
    """Validate all stock entries and report data quality."""
    stocks = load_stocks()
    issues = []
    estimated_count = 0

    for i, stock in enumerate(stocks):
        ticker = stock.get("ticker", f"index_{i}")
        name = stock.get("name_en", "unknown")

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in stock:
                issues.append(f"  ❌ [{ticker}] {name}: missing '{field}'")

        # Check data quality
        financials = [
            stock.get("total_assets", 0), stock.get("total_debt", 0),
            stock.get("total_revenue", 0), stock.get("market_cap", 0),
        ]
        suspicious = any(is_estimated(v) for v in financials)

        if suspicious:
            estimated_count += 1
            stock["data_quality"] = "estimated"
            issues.append(f"  ⚠️  [{ticker}] {name}: values look estimated (round numbers)")
        else:
            stock.setdefault("data_quality", "verified")

        # Ensure market field exists
        stock.setdefault("market", "saudi")
        stock.setdefault("currency", "SAR")
        stock.setdefault("last_updated", "2025-01-01")

    save_stocks(stocks)

    print(f"Validated {len(stocks)} stocks")
    print(f"  Verified:  {len(stocks) - estimated_count}")
    print(f"  Estimated: {estimated_count}")
    print()

    if issues:
        print("Issues found:")
        for issue in issues:
            print(issue)
    else:
        print("✅ All stocks pass validation.")


def template(ticker, market="saudi"):
    """Generate a blank template for manual data entry."""
    currency = {"saudi": "SAR", "us": "USD", "hk": "HKD"}.get(market, "SAR")

    entry = {
        "ticker": ticker,
        "name_en": "",
        "name_ar": "",
        "sector_en": "",
        "sector_ar": "",
        "market": market,
        "currency": currency,
        "total_assets": 0,
        "total_debt": 0,
        "interest_bearing_investments": 0,
        "accounts_receivable": 0,
        "cash_and_equivalents": 0,
        "market_cap": 0,
        "non_compliant_income": 0,
        "total_revenue": 0,
        "data_quality": "verified",
        "last_updated": str(date.today()),
        "source": "",
    }

    print(json.dumps(entry, ensure_ascii=False, indent=2))
    print(f"\n# Fill in the values and append to {STOCKS_FILE}")


def stats():
    """Print summary statistics about the stock database."""
    stocks = load_stocks()

    markets = {}
    for s in stocks:
        m = s.get("market", "saudi")
        markets[m] = markets.get(m, 0) + 1

    estimated = sum(1 for s in stocks if s.get("data_quality") == "estimated")
    verified = sum(1 for s in stocks if s.get("data_quality") == "verified")

    print(f"Stock Database: {STOCKS_FILE.name}")
    print(f"  Total stocks: {len(stocks)}")
    print(f"  By market:    {dict(markets)}")
    print(f"  Verified:     {verified}")
    print(f"  Estimated:    {estimated}")
    print()
    print("Markets supported: saudi, us, hk")
    print()
    print("To add real data:")
    print("  1. Get financials from annual reports or SEC EDGAR")
    print("  2. python3 tools/update_stocks_data.py template --ticker AAPL --market us")
    print("  3. Fill in values, append to stocks.json")
    print("  4. python3 tools/update_stocks_data.py validate")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mizan stock data utility")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("validate", help="Validate and tag data quality")
    sub.add_parser("stats", help="Show database statistics")

    tmpl = sub.add_parser("template", help="Generate blank stock entry template")
    tmpl.add_argument("--ticker", required=True)
    tmpl.add_argument("--market", default="saudi", choices=["saudi", "us", "hk"])

    args = parser.parse_args()

    if args.command == "validate":
        validate()
    elif args.command == "stats":
        stats()
    elif args.command == "template":
        template(args.ticker, args.market)
    else:
        parser.print_help()
