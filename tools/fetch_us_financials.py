#!/usr/bin/env python3
"""fetch_us_financials.py — Automated US stock data fetcher for Mizan.

Pulls real balance sheet data from SEC EDGAR (free, official US government API)
and market data from Yahoo Finance, then maps it to the stocks.json schema
and runs the Sharia screener.

Data Sources:
  - SEC EDGAR CompanyFacts API (data.sec.gov): Balance sheet, income statement
  - Yahoo Finance v8 chart API: Market price, shares outstanding

Usage:
    python3 tools/fetch_us_financials.py fetch AAPL MSFT GOOG
    python3 tools/fetch_us_financials.py fetch-all          # fetch preset list
    python3 tools/fetch_us_financials.py screen             # screen fetched stocks
    python3 tools/fetch_us_financials.py update-stocks-json # merge into stocks.json

Zero external dependencies. Uses only stdlib + curl.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import date

# Paths
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
STOCKS_FILE = PROJECT_DIR / "backend" / "stocks.json"
CACHE_DIR = PROJECT_DIR / "data" / "us_financials_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SEC_HEADERS = "-H 'User-Agent: Mizan-App contact@mizan.app'"
SEC_TIMEOUT = 15
YAHOO_TIMEOUT = 10

# Preset list of popular US stocks to screen
PRESET_TICKERS = [
    "AAPL", "MSFT", "GOOG", "META", "AMZN", "NVDA", "TSLA",
    "JPM", "BAC", "XOM", "JNJ", "WMT", "V", "MA", "UNH",
    "HD", "PG", "COST", "DIS", "NFLX", "AMD", "INTC",
    "CRM", "ADBE", "PFE", "KO", "PEP", "MCD", "NKE",
]

# Fields that screen_company() accepts
SCREENER_FIELDS = [
    "name", "ticker", "sector",
    "total_assets", "total_debt", "interest_bearing_investments",
    "accounts_receivable", "cash_and_equivalents",
    "market_cap", "non_compliant_income", "total_revenue",
]


def curl_json(url, headers="", timeout=15):
    """Fetch JSON via curl, bypassing Python SSL issues."""
    cmd = f"curl -s {headers} '{url}'"
    result = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# SEC EDGAR: Ticker -> CIK mapping
# ---------------------------------------------------------------------------

def load_ticker_map():
    """Load SEC ticker-to-CIK mapping."""
    cache = CACHE_DIR / "tickers.json"
    if cache.exists():
        with open(cache) as f:
            return json.load(f)

    print("  Fetching SEC ticker map...")
    data = curl_json(
        "https://www.sec.gov/files/company_tickers.json",
        SEC_HEADERS
    )
    if not data:
        print("  ❌ Failed to fetch ticker map from SEC")
        return {}

    mapping = {}
    for k, v in data.items():
        mapping[v["ticker"]] = {"cik": v["cik_str"], "title": v["title"]}
    
    with open(cache, "w") as f:
        json.dump(mapping, f, indent=2)
    print(f"  ✓ Loaded {len(mapping)} tickers from SEC")
    return mapping


def get_cik(ticker, ticker_map):
    """Get CIK number for a ticker."""
    info = ticker_map.get(ticker)
    if not info:
        return None
    cik = info["cik"]
    return f"CIK{cik:010d}"


# ---------------------------------------------------------------------------
# SEC EDGAR: CompanyFacts API
# ---------------------------------------------------------------------------

def fetch_company_facts(cik):
    """Fetch full company facts from SEC EDGAR."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/{cik}.json"
    return curl_json(url, SEC_HEADERS, SEC_TIMEOUT)


def extract_latest_annual(gaap_data, concept_names):
    """Try multiple XBRL concept names and return latest annual (10-K) value."""
    if not gaap_data:
        return None, None

    for concept in concept_names:
        if concept not in gaap_data:
            continue
        units = gaap_data[concept].get("units", {})
        for unit_key in ["USD", "shares", "USD/shares"]:
            entries = units.get(unit_key, [])
            annuals = [
                e for e in entries
                if e.get("form") == "10-K" and e.get("fp") == "FY"
            ]
            if annuals:
                latest = annuals[-1]
                return latest["val"], latest.get("end", "")
    
    # Fallback: non-FY 10-K
    for concept in concept_names:
        if concept not in gaap_data:
            continue
        units = gaap_data[concept].get("units", {})
        for unit_key in ["USD", "shares", "USD/shares"]:
            entries = units.get(unit_key, [])
            ten_ks = [e for e in entries if e.get("form") == "10-K"]
            if ten_ks:
                latest = ten_ks[-1]
                return latest["val"], latest.get("end", "")

    return None, None


def parse_sec_financials(facts_data):
    """Extract Sharia-relevant financials from SEC company facts."""
    gaap = facts_data.get("facts", {}).get("us-gaap", {})
    entity = facts_data.get("entityName", "")

    result = {
        "entity_name": entity,
        "total_assets": extract_latest_annual(gaap, ["Assets"]),
        "total_debt": extract_latest_annual(gaap, [
            "LongTermDebt", "Debt", "LongTermDebtNoncurrent", "DebtNoncurrent",
        ]),
        "cash_and_equivalents": extract_latest_annual(gaap, [
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ]),
        "accounts_receivable": extract_latest_annual(gaap, [
            "AccountsReceivableNetCurrent", "AccountsReceivableTradeCurrent",
            "ReceivablesNetCurrent",
        ]),
        "total_revenue": extract_latest_annual(gaap, [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax",
        ]),
        "marketable_securities_current": extract_latest_annual(gaap, [
            "MarketableSecuritiesCurrent",
        ]),
        "marketable_securities_noncurrent": extract_latest_annual(gaap, [
            "MarketableSecuritiesNoncurrent",
        ]),
        "interest_income": extract_latest_annual(gaap, [
            "InvestmentIncomeInterestAndDividend", "InterestIncome",
            "InterestAndDividendIncomeOperating", "InvestmentIncomeInterest",
        ]),
        "short_term_debt": extract_latest_annual(gaap, [
            "DebtCurrent", "ShortTermBorrowings", "CommercialPaper",
        ]),
        "shares_outstanding": extract_latest_annual(gaap, [
            "CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding",
        ]),
    }
    return result


# ---------------------------------------------------------------------------
# Yahoo Finance: Market Price
# ---------------------------------------------------------------------------

def fetch_yahoo_price(ticker):
    """Get current market price from Yahoo Finance v8 chart API."""
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?range=1d&interval=1d"
    )
    data = curl_json(url, "-H 'User-Agent: Mozilla/5.0'", YAHOO_TIMEOUT)
    if not data or "chart" not in data:
        return None
    try:
        meta = data["chart"]["result"][0]["meta"]
        return {
            "price": meta.get("regularMarketPrice"),
            "long_name": meta.get("longName", ""),
            "currency": meta.get("currency", "USD"),
            "exchange": meta.get("exchangeName", ""),
        }
    except (KeyError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Build Stock Entry
# ---------------------------------------------------------------------------

def _safe_val(sec_data, key):
    """Extract numeric value, handling (value, date) tuples or None."""
    v = sec_data.get(key)
    if v is None:
        return 0
    if isinstance(v, tuple):
        return v[0] if v[0] is not None else 0
    if isinstance(v, (int, float)):
        return v
    return 0


def build_stock_entry(ticker, sec_data, yahoo_data):
    """Build a stocks.json-compatible entry from fetched data."""
    total_assets = _safe_val(sec_data, "total_assets")
    long_term_debt = _safe_val(sec_data, "total_debt")
    short_term_debt = _safe_val(sec_data, "short_term_debt")
    total_debt = long_term_debt + short_term_debt
    cash = _safe_val(sec_data, "cash_and_equivalents")
    receivables = _safe_val(sec_data, "accounts_receivable")
    revenue = _safe_val(sec_data, "total_revenue")
    interest_income = _safe_val(sec_data, "interest_income")

    mkt_sec_current = _safe_val(sec_data, "marketable_securities_current")
    mkt_sec_noncurrent = _safe_val(sec_data, "marketable_securities_noncurrent")
    interest_bearing_investments = mkt_sec_current + mkt_sec_noncurrent

    shares = _safe_val(sec_data, "shares_outstanding")
    price = yahoo_data.get("price", 0) if yahoo_data else 0
    market_cap = int(shares * price) if shares and price else 0

    non_compliant_income = interest_income

    fy_end = ""
    for key in ["total_assets", "total_revenue"]:
        v = sec_data.get(key)
        if v and isinstance(v, tuple) and v[1]:
            fy_end = v[1][:7]
            break

    entry = {
        "ticker": ticker,
        "name_en": yahoo_data.get("long_name", "") if yahoo_data else sec_data.get("entity_name", ""),
        "name_ar": "",
        "sector_en": "",
        "sector_ar": "",
        "market": "us",
        "currency": "USD",
        "total_assets": total_assets,
        "total_debt": total_debt,
        "interest_bearing_investments": interest_bearing_investments,
        "accounts_receivable": receivables,
        "cash_and_equivalents": cash,
        "market_cap": market_cap,
        "non_compliant_income": non_compliant_income,
        "total_revenue": revenue,
        "data_quality": "verified",
        "last_updated": str(date.today()),
        "source": "SEC EDGAR + Yahoo Finance",
        "fy_end": fy_end,
    }
    return entry


# ---------------------------------------------------------------------------
# Cache management (accumulate, not overwrite)
# ---------------------------------------------------------------------------

def load_cache():
    """Load cached stocks, returning {ticker: entry} dict."""
    cache_file = CACHE_DIR / "fetched_stocks.json"
    if cache_file.exists():
        with open(cache_file) as f:
            stocks = json.load(f)
        return {s["ticker"]: s for s in stocks}
    return {}


def save_cache(stocks_dict):
    """Save cache as a list."""
    cache_file = CACHE_DIR / "fetched_stocks.json"
    with open(cache_file, "w") as f:
        json.dump(list(stocks_dict.values()), f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_fetch(tickers):
    """Fetch financial data for given tickers. Accumulates into cache."""
    ticker_map = load_ticker_map()
    cache = load_cache()
    new_count = 0

    for ticker in tickers:
        print(f"\n--- {ticker} ---")
        cik = get_cik(ticker, ticker_map)
        if not cik:
            print(f"  ❌ Ticker not found in SEC database")
            continue

        print(f"  CIK: {cik}")
        print(f"  Fetching SEC company facts...")
        facts = fetch_company_facts(cik)
        if not facts:
            print(f"  ❌ Failed to fetch from SEC EDGAR")
            continue

        sec_data = parse_sec_financials(facts)
        print(f"  Entity: {sec_data['entity_name']}")

        print(f"  Fetching Yahoo Finance price...")
        yahoo = fetch_yahoo_price(ticker)
        if yahoo:
            print(f"  Price: ${yahoo['price']} ({yahoo['currency']})")

        entry = build_stock_entry(ticker, sec_data, yahoo)
        cache[ticker] = entry
        new_count += 1

        print(f"  Total Assets:      ${entry['total_assets']:,.0f}")
        print(f"  Total Debt:        ${entry['total_debt']:,.0f}")
        print(f"  Cash:              ${entry['cash_and_equivalents']:,.0f}")
        print(f"  Revenue:           ${entry['total_revenue']:,.0f}")
        print(f"  Market Cap:        ${entry['market_cap']:,.0f}")

        time.sleep(0.2)  # SEC rate limit: max 10 req/sec

    save_cache(cache)
    print(f"\n✅ Fetched {new_count} new stocks. Cache now has {len(cache)} total → {CACHE_DIR / 'fetched_stocks.json'}")


def cmd_fetch_all():
    """Fetch all preset tickers."""
    print(f"Fetching {len(PRESET_TICKERS)} US stocks from SEC EDGAR...")
    cmd_fetch(PRESET_TICKERS)


def _run_screener(stock):
    """Call screen_company with properly unpacked kwargs."""
    sys.path.insert(0, str(TOOLS_DIR))
    from sharia_screener import screen_company

    kwargs = {}
    for field in SCREENER_FIELDS:
        if field == "name":
            kwargs["name"] = stock.get("name_en", stock.get("ticker", ""))
        elif field == "sector":
            kwargs["sector"] = stock.get("sector_en", "")
        else:
            kwargs[field] = stock.get(field, 0)

    return screen_company(**kwargs)


def cmd_screen(tickers=None):
    """Run Sharia screener on fetched stocks."""
    cache = load_cache()
    stocks = list(cache.values())

    if tickers:
        stocks = [s for s in stocks if s["ticker"] in tickers]

    if not stocks:
        print("❌ No cached data. Run 'fetch' first.")
        return

    print(f"\n{'='*70}")
    print(f"Sharia Screening Results: {len(stocks)} US Stocks (SEC EDGAR data)")
    print(f"{'='*70}\n")

    halal = []
    haram = []

    for stock in stocks:
        result = _run_screener(stock)
        verdict = result.get("verdict", "UNKNOWN")
        ticker = stock["ticker"]
        name = stock.get("name_en", ticker)[:35]

        qs = result.get("quantitative_screen", {}) or {}
        ratios = {k: v for k, v in qs.items() if isinstance(v, dict)}
        if verdict == "NON-COMPLIANT":
            haram.append((ticker, name, result))
            icon = "🚫"
        elif verdict == "COMPLIANT":
            halal.append((ticker, name, result))
            icon = "✅"
        else:
            halal.append((ticker, name, result))
            icon = "⚠️"

        print(f"{icon} {ticker:5s} {name}")
        for rname, rdata in ratios.items():
            val = rdata.get("value", 0)
            thresh = rdata.get("threshold", 0)
            passed = "✓" if rdata.get("passed") else "✗"
            print(f"   {passed} {rname}: {val:.1f}% (limit {thresh:.0f}%)")
        print()

    print(f"{'='*70}")
    print(f"SUMMARY: {len(halal)} halal, {len(haram)} non-compliant out of {len(stocks)}")
    print(f"{'='*70}")
    if halal:
        print(f"\n✅ Sharia-Compliant:")
        for ticker, name, _ in halal:
            print(f"  ✅ {ticker}: {name}")
    if haram:
        print(f"\n🚫 Non-Compliant:")
        for ticker, name, _ in haram:
            print(f"  🚫 {ticker}: {name}")


def cmd_update_stocks_json():
    """Merge fetched US stocks into the main stocks.json."""
    cache = load_cache()
    us_stocks = list(cache.values())

    if not us_stocks:
        print("❌ No cached data. Run 'fetch-all' first.")
        return

    with open(STOCKS_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)

    saudi_only = [s for s in existing if s.get("market") != "us"]
    combined = saudi_only + us_stocks

    with open(STOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"✅ Updated {STOCKS_FILE.name}")
    print(f"   Saudi stocks: {len(saudi_only)}")
    print(f"   US stocks:    {len(us_stocks)}")
    print(f"   Total:        {len(combined)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch real US stock financials from SEC EDGAR + Yahoo Finance"
    )
    sub = parser.add_subparsers(dest="command")

    f = sub.add_parser("fetch", help="Fetch specific tickers")
    f.add_argument("tickers", nargs="+", help="Ticker symbols")

    sub.add_parser("fetch-all", help="Fetch preset list of 29 popular stocks")

    sc = sub.add_parser("screen", help="Screen fetched stocks for Sharia compliance")
    sc.add_argument("tickers", nargs="*", help="Optional: only screen these tickers")

    sub.add_parser("update-stocks-json", help="Merge fetched data into stocks.json")

    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch(args.tickers)
    elif args.command == "fetch-all":
        cmd_fetch_all()
    elif args.command == "screen":
        cmd_screen(args.tickers if args.tickers else None)
    elif args.command == "update-stocks-json":
        cmd_update_stocks_json()
    else:
        parser.print_help()
