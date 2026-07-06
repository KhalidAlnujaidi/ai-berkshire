#!/usr/bin/env python3
"""Expand the stock database to full Tadawul coverage.

Fetches the company directory from Tadawul (via Playwright scraper),
pulls financial data for each main-market stock via yfinance, runs the
AAOIFI Sharia screening, and writes a new stocks.json.

Usage:
    python3 expand_tadawul.py [--dry-run] [--limit N] [--output stocks.json]

Produces a stocks.json compatible with the existing backend API.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

# Add backend dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sharia_screener import screen_company, screen_sector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Sector mapping (Yahoo Finance → our sectors) ────────────────────────────

YAHOO_SECTOR_MAP = {
    "Financial Services": "Financial Services",
    "Energy": "Energy",
    "Basic Materials": "Basic Materials",
    "Communication Services": "Telecommunications",
    "Technology": "Technology",
    "Consumer Cyclical": "Consumer Cyclical",
    "Consumer Defensive": "Consumer Defensive",
    "Healthcare": "Healthcare",
    "Industrials": "Industrials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
    "Materials": "Basic Materials",
    "Consumer Non-Durables": "Consumer Defensive",
}

SECTOR_AR_MAP = {
    "Financial Services": "الخدمات المالية",
    "Energy": "الطاقة",
    "Basic Materials": "المواد الأساسية",
    "Telecommunications": "الاتصالات",
    "Technology": "التقنية",
    "Consumer Cyclical": "الاستهلاكية الدورية",
    "Consumer Defensive": "الاستهلاكية الأساسية",
    "Healthcare": "الرعاية الصحية",
    "Industrials": "الصناعات",
    "Real Estate": "العقارات",
    "Utilities": "المرافق",
    "Islamic Banking": "الخدمات المصرفية الإسلامية",
    "Petrochemicals": "البتروكيماويات",
    "Retail": "التجزئة",
    "Transportation": "النقل",
    "Insurance": "التأمين",
    "Agriculture": "الزراعة",
    "Media": "الإعلام",
    "Construction": "الإنشاء",
    "Investment": "الاستثمار",
}

# Saudi-sector-based Sharia classification for known Islamic institutions
ISLAMIC_INSTITUTIONS = {
    # Islamic banks — interest income = 0 by design
    "1120": "islamic_bank",  # Al Rajhi Bank
    "1180": "conventional_bank",  # Saudi National Bank
    "1020": "conventional_bank",  # Riyad Bank
    "1050": "conventional_bank",  # Saudi Awwal Bank (SABB)
    "1060": "conventional_bank",  # Bank Albilad (but purports Islamic)
    "1150": "conventional_bank",  # Saudi Investment Bank (SAIB)
    "5110": "conventional_bank",  # Alinma Bank
    "7010": "telecom",  # STC
    "2222": "energy",  # Aramco
    "2010": "petrochemicals",  # SABIC
    "2280": "petrochemicals",  # Saudi Aramco Base Oil
    "2380": "petrochemicals",  # Aldawaa Medical
}


def get_saudi_sector(yahoo_sector: str, ticker: str) -> tuple[str, str]:
    """Return (sector_en, sector_ar) for a Saudi stock."""
    # Special cases for Islamic banks
    if ticker == "1120":
        return ("Islamic Banking", SECTOR_AR_MAP["Islamic Banking"])
    
    # For conventional banks, mark as conventional banking (haram)
    if ticker in ("1180", "1020", "1050", "1150", "5110"):
        return ("Conventional Banking", "الخدمات المصرفية التقليدية")
    if ticker in ("8090", "8020", "8010", "8050", "8070"):
        # Insurance companies
        return ("Insurance", SECTOR_AR_MAP.get("Insurance", "التأمين"))
    
    sector_en = YAHOO_SECTOR_MAP.get(yahoo_sector, yahoo_sector or "Unknown")
    sector_ar = SECTOR_AR_MAP.get(sector_en, "غير محدد")
    return (sector_en, sector_ar)


def fetch_yf_data(ticker_sr: str) -> dict | None:
    """Fetch financial data from Yahoo Finance for a single .SR ticker."""
    try:
        import yfinance as yf
        
        t = yf.Ticker(ticker_sr)
        info = t.info or {}
        
        # Get balance sheet for total assets + receivables
        total_assets = info.get("totalAssets")
        total_debt = info.get("totalDebt")
        total_revenue = info.get("totalRevenue")
        total_cash = info.get("totalCash")
        market_cap = info.get("marketCap")
        receivables = info.get("receivables")
        
        # If total_assets not in info, try balance sheet
        if not total_assets or not receivables:
            try:
                bs = t.balance_sheet
                if bs is not None and not bs.empty:
                    col = bs.columns[0]
                    if not total_assets and "Total Assets" in bs.index:
                        total_assets = float(bs.loc["Total Assets", col])
                    if not receivables and "Accounts Receivable" in bs.index:
                        receivables = float(bs.loc["Accounts Receivable", col])
                    elif not receivables and "Receivables" in bs.index:
                        receivables = float(bs.loc["Receivables", col])
                    if not total_debt and "Total Debt" in bs.index:
                        total_debt = float(bs.loc["Total Debt", col])
                    if not total_cash and "Cash And Cash Equivalents" in bs.index:
                        total_cash = float(bs.loc["Cash And Cash Equivalents", col])
            except Exception as e:
                logger.debug(f"  balance_sheet for {ticker_sr}: {e}")
        
        return {
            "shortName": info.get("shortName", ""),
            "longName": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "marketCap": market_cap,
            "totalAssets": total_assets,
            "totalDebt": total_debt,
            "totalRevenue": total_revenue,
            "totalCash": total_cash,
            "receivables": receivables,
        }
    except Exception as e:
        logger.warning(f"  yfinance {ticker_sr}: {e}")
        return None


def _clean_num(val) -> float:
    """Convert a value from yfinance to a clean float (0 for NaN/None)."""
    if val is None:
        return 0
    try:
        f = float(val)
        return 0 if f != f else f  # NaN → 0
    except (ValueError, TypeError):
        return 0


def screen_stock(
    ticker: str,
    name_en: str,
    name_ar: str,
    sector_en: str,
    sector_ar: str,
    yf_data: dict,
) -> dict:
    """Run Sharia screening and build the stock record."""
    total_assets = _clean_num(yf_data.get("totalAssets"))
    total_debt = _clean_num(yf_data.get("totalDebt"))
    total_cash = _clean_num(yf_data.get("totalCash"))
    receivables = _clean_num(yf_data.get("receivables"))
    market_cap = _clean_num(yf_data.get("marketCap"))
    total_revenue = _clean_num(yf_data.get("totalRevenue"))
    
    # Run Sharia screen
    result = screen_company(
        name=name_en,
        ticker=ticker,
        sector=sector_en,
        total_assets=total_assets,
        total_debt=total_debt,
        interest_bearing_investments=0,  # Hard to get from YF; most non-bank SA stocks have 0
        accounts_receivable=receivables,
        cash_and_equivalents=total_cash,
        market_cap=market_cap,
        non_compliant_income=0,
        total_revenue=total_revenue,
    )
    
    verdict = result["verdict"]
    verdict_detail = result["verdict_detail"]
    
    # Determine data quality
    if total_assets > 0 and total_debt > 0:
        data_quality = "verified"
    elif market_cap > 0:
        data_quality = "partial"
    else:
        data_quality = "limited"
    
    return {
        "ticker": ticker,
        "name_ar": name_ar,
        "name_en": name_en,
        "sector_ar": sector_ar,
        "sector_en": sector_en,
        "total_assets": total_assets,
        "total_debt": total_debt,
        "interest_bearing_investments": 0,
        "accounts_receivable": receivables,
        "cash_and_equivalents": total_cash,
        "market_cap": market_cap,
        "non_compliant_income": 0,
        "total_revenue": total_revenue,
        "data_quality": data_quality,
        "market": "saudi",
        "currency": "SAR",
        "last_updated": date.today().isoformat(),
        "data_source": "Yahoo Finance + Tadawul directory",
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "quantitative_screen": result.get("quantitative_screen"),
    }


def load_existing_us_stocks() -> list[dict]:
    """Load existing US stocks from stocks.json (keep them as-is)."""
    stocks_path = Path(__file__).resolve().parent / "stocks.json"
    if not stocks_path.exists():
        return []
    with open(stocks_path) as f:
        stocks = json.load(f)
    return [s for s in stocks if s.get("market") == "us"]


def get_tadawul_directory() -> list[dict]:
    """Fetch company directory from Tadawul scraper."""
    try:
        from tadawul_scraper import get_company_directory
        companies = get_company_directory()
        if companies:
            main_market = [c for c in companies if c.get("market_type") == "M"]
            logger.info(f"Tadawul: {len(main_market)} main market companies")
            return main_market
    except Exception as e:
        logger.error(f"Tadawul scraper failed: {e}")
    return []


def main():
    parser = argparse.ArgumentParser(description="Expand stock DB to full Tadawul")
    parser.add_argument("--dry-run", action="store_true", help="Don't write output")
    parser.add_argument("--limit", type=int, default=0, help="Limit to N stocks (0 = all)")
    parser.add_argument("--output", default="stocks.json", help="Output file")
    parser.add_argument("--keep-us", action="store_true", default=True, help="Keep existing US stocks")
    args = parser.parse_args()
    
    output_path = Path(__file__).resolve().parent / args.output
    
    # Step 1: Get Tadawul directory
    logger.info("Step 1: Fetching Tadawul company directory...")
    companies = get_tadawul_directory()
    if not companies:
        logger.error("No companies from Tadawul — aborting")
        sys.exit(1)
    
    if args.limit > 0:
        companies = companies[:args.limit]
        logger.info(f"Limited to {len(companies)} companies")
    
    # Step 2: Fetch financial data + screen each stock
    logger.info(f"Step 2: Fetching Yahoo Finance data for {len(companies)} stocks...")
    sa_stocks = []
    stats = {"success": 0, "failed": 0, "partial": 0, "compliant": 0, "non_compliant": 0}
    
    for i, company in enumerate(companies, 1):
        ticker = company["symbol"]
        name_en = company.get("trading_name_en") or company.get("name_en", ticker)
        name_ar = company.get("trading_name_ar") or company.get("name_ar", ticker)
        
        logger.info(f"  [{i}/{len(companies)}] {ticker}: {name_en}")
        
        # Fetch from Yahoo Finance
        yf_data = fetch_yf_data(f"{ticker}.SR")
        if yf_data is None:
            stats["failed"] += 1
            # Still add with limited data — sector-only screening
            sector_en, sector_ar = get_saudi_sector("", ticker)
            stock = {
                "ticker": ticker,
                "name_ar": name_ar,
                "name_en": name_en,
                "sector_ar": sector_ar,
                "sector_en": sector_en,
                "total_assets": 0,
                "total_debt": 0,
                "interest_bearing_investments": 0,
                "accounts_receivable": 0,
                "cash_and_equivalents": 0,
                "market_cap": 0,
                "non_compliant_income": 0,
                "total_revenue": 0,
                "data_quality": "limited",
                "market": "saudi",
                "currency": "SAR",
                "last_updated": date.today().isoformat(),
                "data_source": "Tadawul directory only",
                "verdict": "NON-COMPLIANT" if sector_en == "Conventional Banking" else "COMPLIANT",
                "verdict_detail": "Limited data — sector-based screening only." if sector_en != "Conventional Banking" else "Prohibited business activity.",
            }
            sa_stocks.append(stock)
            if stock["verdict"] == "COMPLIANT":
                stats["compliant"] += 1
            else:
                stats["non_compliant"] += 1
            time.sleep(0.3)
            continue
        
        # Use Yahoo sector if available
        yahoo_sector = yf_data.get("sector", "")
        sector_en, sector_ar = get_saudi_sector(yahoo_sector, ticker)
        
        # Use Yahoo name if better
        if yf_data.get("shortName"):
            name_en = yf_data["shortName"]
        if yf_data.get("longName") and not name_ar:
            name_ar = yf_data.get("longName", name_ar)
        
        stock = screen_stock(ticker, name_en, name_ar, sector_en, sector_ar, yf_data)
        sa_stocks.append(stock)
        
        if stock["data_quality"] == "verified":
            stats["success"] += 1
        else:
            stats["partial"] += 1
        
        if stock["verdict"] == "COMPLIANT":
            stats["compliant"] += 1
        else:
            stats["non_compliant"] += 1
        
        # Rate limit: yfinance can handle ~2 req/s
        time.sleep(0.5)
    
    logger.info(f"  Done: {stats['success']} verified, {stats['partial']} partial, {stats['failed']} failed")
    logger.info(f"  Sharia: {stats['compliant']} compliant, {stats['non_compliant']} non-compliant")
    
    # Step 3: Merge with existing US stocks
    all_stocks = sa_stocks
    if args.keep_us:
        us_stocks = load_existing_us_stocks()
        all_stocks = sa_stocks + us_stocks
        logger.info(f"Step 3: Merged with {len(us_stocks)} US stocks → {len(all_stocks)} total")
    else:
        logger.info(f"Step 3: {len(all_stocks)} Saudi stocks (US stocks excluded)")
    
    # Step 4: Write output
    if args.dry_run:
        logger.info("Dry run — not writing file")
        print(json.dumps(all_stocks[:5], indent=2, ensure_ascii=False))
    else:
        with open(output_path, "w") as f:
            json.dump(all_stocks, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(all_stocks)} stocks to {output_path}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  Tadawul Expansion Summary")
    print(f"{'='*60}")
    print(f"  Saudi stocks: {len(sa_stocks)}")
    print(f"  US stocks:    {len(us_stocks) if args.keep_us else 0}")
    print(f"  Total:        {len(all_stocks)}")
    print(f"  Halal:        {stats['compliant']}")
    print(f"  Non-compliant: {stats['non_compliant']}")
    print(f"  Verified data: {stats['success']}")
    print(f"  Partial data:  {stats['partial']}")
    print(f"  Failed fetch:  {stats['failed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
