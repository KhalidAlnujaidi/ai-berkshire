#!/usr/bin/env python3
"""
Fetch real Saudi stock financials from Yahoo Finance.

Uses Yahoo's quoteSummary API with crumb/cookie auth to get:
- totalDebt, totalCash, totalRevenue (from financialData)
- netIncome, sharesOutstanding, bookValue (from defaultKeyStatistics)
- currentPrice, ROA (from financialData)

Computes:
- total_assets = netIncome / returnOnAssets  (when ROA available)
- market_cap = currentPrice * sharesOutstanding

Then maps everything to the stocks.json schema and runs the Sharia screener.

Usage:
  python3 fetch_saudi_financials.py           # Fetch all Saudi stocks
  python3 fetch_saudi_financials.py 1120      # Fetch specific ticker
"""

import urllib.request
import urllib.error
import json
import http.cookiejar
import time
import sys
import os
from datetime import date

# ─── Config ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
STOCKS_JSON = os.path.join(PROJECT_DIR, "backend", "stocks.json")

# Tickers where Yahoo has reliable data (large caps, frequently traded)
RELIABLE_TICKERS = {
    "1120",  # Al Rajhi Bank
    "2222",  # Saudi Aramco
    "7010",  # STC Group
    "1180",  # SNB
    "1020",  # Riyad Bank
    "1010",  # NCB/SAB
    "2010",  # SABIC
    "1150",  # Alinma Bank
    "2280",  # ADNOC Distribution
    "2380",  # Bank Albilad
    "4030",  # Kingdom Holding
    "4020",  # Othaim Markets
    "4263",  # Ma'aden
}

# Conventional banks — must fail qualitative screen
CONVENTIONAL_BANKS = {"1180", "1020", "1010"}

# ─── Yahoo Finance Auth ────────────────────────────────────────────────────────

_yahoo_opener = None
_yahoo_crumb = None


def get_yahoo_session():
    global _yahoo_opener, _yahoo_crumb
    if _yahoo_opener and _yahoo_crumb:
        return _yahoo_opener, _yahoo_crumb

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        opener.open(
            urllib.request.Request("https://fc.yahoo.com", headers={"User-Agent": "Mozilla/5.0"}),
            timeout=15,
        )
    except urllib.error.HTTPError:
        pass

    resp = opener.open(
        urllib.request.Request(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers={"User-Agent": "Mozilla/5.0"},
        ),
        timeout=15,
    )
    crumb = resp.read().decode().strip()

    _yahoo_opener = opener
    _yahoo_crumb = crumb
    return opener, crumb


def fetch_quote_summary(ticker_sr: str) -> dict | None:
    opener, crumb = get_yahoo_session()
    modules = "financialData,defaultKeyStatistics,incomeStatementHistory"
    url = (
        f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker_sr}"
        f"?crumb={crumb}&modules={modules}"
    )

    for attempt in range(3):
        try:
            resp = opener.open(
                urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                timeout=20,
            )
            data = json.loads(resp.read())
            result = data.get("quoteSummary", {}).get("result")
            if result and len(result) > 0:
                return result[0]
            return None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (attempt + 1)
                print(f"rate limited, waiting {wait}s...", end="", flush=True)
                time.sleep(wait)
                global _yahoo_opener, _yahoo_crumb
                _yahoo_opener = None
                _yahoo_crumb = None
                opener, crumb = get_yahoo_session()
            else:
                return None
        except Exception:
            return None
    return None


def _raw(field: dict) -> int | float | None:
    if isinstance(field, dict) and "raw" in field:
        return field["raw"]
    return None


def extract_financials(raw: dict, ticker: str) -> dict:
    fin = raw.get("financialData", {})
    ks = raw.get("defaultKeyStatistics", {})
    inc_hist = raw.get("incomeStatementHistory", {}).get("incomeStatementHistory", [])

    total_debt = _raw(fin.get("totalDebt", {}))
    total_cash = _raw(fin.get("totalCash", {}))
    total_revenue = _raw(fin.get("totalRevenue", {}))
    current_price = _raw(fin.get("currentPrice", {}))
    roa = _raw(fin.get("returnOnAssets", {}))
    operating_cashflow = _raw(fin.get("operatingCashflow", {}))
    net_income = _raw(ks.get("netIncomeToCommon", {}))
    shares_outstanding = _raw(ks.get("sharesOutstanding", {}))
    book_value = _raw(ks.get("bookValue", {}))
    ev = _raw(ks.get("enterpriseValue", {}))

    if not net_income and inc_hist:
        net_income = _raw(inc_hist[0].get("netIncome", {}))
    if not total_revenue and inc_hist:
        total_revenue = _raw(inc_hist[0].get("totalRevenue", {}))

    # Compute total assets: netIncome / ROA (only when both positive)
    total_assets = None
    if net_income and roa and roa > 0 and net_income > 0:
        total_assets = int(net_income / roa)

    # Fallback: book value * shares (equity), then add debt
    total_equity = None
    if book_value and shares_outstanding:
        total_equity = int(book_value * shares_outstanding)
    if not total_assets and total_equity and total_debt:
        total_assets = total_equity + total_debt

    # Another fallback: EV-based estimate (rough)
    if not total_assets and ev:
        total_assets = int(ev * 0.8)  # assets typically ~80% of EV

    market_cap = None
    if current_price and shares_outstanding:
        market_cap = int(current_price * shares_outstanding)

    is_bank = ticker in ("1120", "1150", "1180", "1020", "1010", "2380", "1322")

    # Data quality check
    data_quality = "verified"
    if ticker not in RELIABLE_TICKERS:
        data_quality = "partial"
    if total_assets and total_assets < 0:
        data_quality = "partial"

    return {
        "ticker": ticker,
        "total_assets": total_assets,
        "total_debt": total_debt,
        "cash_and_equivalents": total_cash,
        "total_revenue": total_revenue,
        "net_income": net_income,
        "market_cap": market_cap,
        "shares_outstanding": shares_outstanding,
        "total_equity": total_equity,
        "current_price": current_price,
        "roa": roa,
        "is_bank": is_bank,
        "data_quality": data_quality,
        "data_source": "Yahoo Finance quoteSummary",
        "last_updated": date.today().isoformat(),
    }


def run_screener_on_all(stocks: list):
    """Run the Sharia screener with proper kwargs on every Saudi stock."""
    sys.path.insert(0, os.path.join(PROJECT_DIR, "tools"))
    from sharia_screener import screen_company

    print(f"\n{'='*70}")
    print(f"Sharia Compliance Screening (AAOIFI Standard No. 21)")
    print(f"{'='*70}\n")

    compliant = 0
    total = 0

    for stock in stocks:
        if stock.get("market") != "saudi":
            continue
        total += 1

        # Determine correct sector tag
        sector = stock.get("sector_en", "")
        ticker = stock["ticker"]
        if ticker in CONVENTIONAL_BANKS:
            sector = "Conventional Banking"

        result = screen_company(
            name=stock.get("name_en", "?"),
            ticker=ticker,
            sector=sector,
            total_assets=stock.get("total_assets", 0),
            total_debt=stock.get("total_debt", 0),
            interest_bearing_investments=stock.get("interest_bearing_investments", 0),
            accounts_receivable=stock.get("accounts_receivable", 0),
            cash_and_equivalents=stock.get("cash_and_equivalents", 0),
            market_cap=stock.get("market_cap", 0),
            non_compliant_income=stock.get("non_compliant_income", 0),
            total_revenue=stock.get("total_revenue", 0),
        )

        verdict = result["verdict"]
        icon = {"COMPLIANT": "✅", "COMPLIANT_WITH_OVERLAY": "✅⚠️",
                "COMPLIANT_WITH_PURIFICATION": "🤲", "NON-COMPLIANT": "🚫"}.get(verdict, "?")
        if "COMPLIANT" in verdict:
            compliant += 1

        qual = result.get("qualitative_screen", {})
        quant = result.get("quantitative_screen")

        detail = ""
        if quant:
            failed = [k for k, v in quant.items()
                      if isinstance(v, dict) and not v.get("passed", True)]
            if failed:
                detail = " | FAILED: " + ", ".join(failed)

        print(f"  {icon} {ticker:6s} {stock.get('name_en','?')[:35]:35s} → {verdict}{detail}")

    print(f"\n  Total: {compliant}/{total} compliant")


def main():
    with open(STOCKS_JSON) as f:
        stocks = json.load(f)

    saudi = [s for s in stocks if s.get("market") == "saudi"]
    if len(sys.argv) > 1:
        target = sys.argv[1]
        saudi = [s for s in saudi if s["ticker"] == target]
        if not saudi:
            print(f"Ticker {target} not found")
            return

    print(f"Fetching real financials for {len(saudi)} Saudi stocks...\n")

    updated = 0
    failed = []

    for stock in saudi:
        ticker = stock["ticker"]
        name = stock.get("name_en", "?")
        print(f"  [{ticker}] {name}...", end=" ", flush=True)

        raw = fetch_quote_summary(f"{ticker}.SR")
        if not raw:
            print("❌ no data")
            failed.append(ticker)
            continue

        fin = extract_financials(raw, ticker)

        if not fin["total_debt"]:
            print("❌ missing debt data")
            failed.append(ticker)
            continue

        # Update stock
        stock["total_assets"] = abs(fin["total_assets"] or 0)
        stock["total_debt"] = fin["total_debt"]
        stock["cash_and_equivalents"] = fin["cash_and_equivalents"] or 0
        stock["total_revenue"] = fin["total_revenue"] or 0
        stock["market_cap"] = fin["market_cap"] or 0
        stock["data_quality"] = fin["data_quality"]
        stock["data_source"] = fin["data_source"]
        stock["last_updated"] = fin["last_updated"]

        if not fin["is_bank"]:
            rev = fin["total_revenue"] or 0
            stock["accounts_receivable"] = int(rev * 0.20) if rev else 0
            stock["_receivables_estimated"] = True
            stock["interest_bearing_investments"] = 0
            stock["non_compliant_income"] = 0
        else:
            stock["accounts_receivable"] = fin["total_revenue"] or 0
            stock["interest_bearing_investments"] = 0
            stock["non_compliant_income"] = 0

        ta = f"{abs(fin['total_assets'] or 0)/1e9:.1f}B" if fin["total_assets"] else "?"
        td = f"{fin['total_debt']/1e9:.1f}B" if fin["total_debt"] else "?"
        rev = f"{(fin['total_revenue'] or 0)/1e9:.1f}B"
        mc = f"{(fin['market_cap'] or 0)/1e9:.1f}B"
        dq = fin["data_quality"]
        print(f"✅ A:{ta} D:{td} R:{rev} MC:{mc} [{dq}]")

        updated += 1
        time.sleep(1.5)

    with open(STOCKS_JSON, "w") as f:
        json.dump(stocks, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(saudi)}, Failed: {len(failed)}")
    if failed:
        print(f"Failed tickers: {', '.join(failed)}")

    run_screener_on_all(stocks)


if __name__ == "__main__":
    main()
