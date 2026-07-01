"""Tadawul (Saudi Exchange) scraper via Playwright.

saudiexchange.sa is behind Akamai edge security which blocks all non-browser
requests (curl, requests, httpx all get 403). This module uses Playwright in
headed mode (under xvfb) to bypass the bot detection, then fetches JSON data
from the site's internal servlet APIs within the browser context.

Data sources discovered (all at https://www.saudiexchange.sa/tadawul.eportal.theme.helper/):
  - TickerServlet             → live market data for all 398 listed instruments
  - ThemeSearchUtilityServlet → company directory (1871 entries: symbols, names, ISIN)
  - ThemeTASIUtilityServlet   → TASI/MT30/NOMUC/Sukuk index data, market status

Architecture:
  - One Playwright browser launch per scrape session (expensive ~2-3s)
  - Browser navigates to home page (bypasses Akamai, establishes session)
  - JSON APIs are fetched via in-browser fetch() — shares the same Akamai-cleared session
  - Results are cached in-memory with a TTL (default 5 minutes)
  - All fetches fail-soft: return cached/stale data on error, never raise

Usage:
  from tadawul_scraper import get_all_stock_prices, get_company_directory, get_market_summary

  prices = get_all_stock_prices()       # {ticker: {price, volume, ...}}
  companies = get_company_directory()   # [{symbol, name_en, name_ar, isin, market_type}, ...]
  summary = get_market_summary()        # {tasi_value, tasi_change, advancers, decliners, ...}
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 300  # 5 minutes
BROWSER_TIMEOUT = 30_000  # 30 seconds
BASE_URL = "https://www.saudiexchange.sa"
SERVLET_PATH = "/tadawul.eportal.theme.helper"

# ── In-memory cache ──────────────────────────────────────────────────────────

_cache: dict[str, tuple[float, Any]] = {}  # key -> (timestamp, data)


def _now() -> float:
    return time.monotonic()


def clear_cache(key: str | None = None) -> None:
    """Clear the scraper cache. If key given, clear only that entry."""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()


def _get_cached(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, data = entry
    if _now() - ts > CACHE_TTL_SECONDS:
        return None
    if isinstance(data, dict):
        return {**data, "cached": True}
    if isinstance(data, list):
        return data
    return data


def _get_stale(key: str) -> Any | None:
    """Return stale cached data even if expired (fail-soft fallback)."""
    entry = _cache.get(key)
    if entry is None:
        return None
    _, data = entry
    if isinstance(data, dict):
        return {**data, "cached": True, "stale": True}
    return data


def _set_cache(key: str, data: Any) -> None:
    _cache[key] = (_now(), data)


# ── Playwright browser management ────────────────────────────────────────────

_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
"""


def _is_xvfb_running() -> bool:
    """Check if an X display (real or xvfb) is available."""
    return bool(os.environ.get("DISPLAY"))


@contextmanager
def _playwright_session():
    """Context manager that yields a Playwright page with Akamai bypass.

    Launches Chromium in headed mode. Caller must ensure DISPLAY is set
    (typically via xvfb-run). If no display is available, we auto-launch xvfb.
    """
    from playwright.sync_api import sync_playwright

    # Auto-launch xvfb if no display
    xvfb_proc = None
    if not _is_xvfb_running():
        xvfb_proc = subprocess.Popen(
            ["Xvfb", ":99", "-screen", "0", "1920x1080x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.environ["DISPLAY"] = ":99"
        time.sleep(1)  # Give xvfb time to start

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=False,  # Headed — required for Akamai bypass
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            context.add_init_script(_STEALTH_JS)
            page = context.new_page()

            # Navigate to home to establish session (bypasses Akamai)
            page.goto(BASE_URL, timeout=BROWSER_TIMEOUT, wait_until="networkidle")
            page.wait_for_timeout(1000)

            try:
                yield page
            finally:
                context.close()
                browser.close()
    finally:
        if xvfb_proc:
            xvfb_proc.terminate()
            xvfb_proc.wait(timeout=5)


def _fetch_servlet_json(page, servlet_name: str) -> Any | None:
    """Fetch JSON from a Tadawul servlet via in-browser fetch()."""
    js = f"""async () => {{
        const resp = await fetch('{SERVLET_PATH}/{servlet_name}', {{
            headers: {{'Accept': 'application/json'}}
        }});
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return await resp.json();
    }}"""
    try:
        return page.evaluate(js)
    except Exception as e:
        logger.warning(f"Tadawul {servlet_name}: fetch failed: {e}")
        return None


# ── Public API ───────────────────────────────────────────────────────────────

def get_all_stock_prices() -> dict[str, dict] | None:
    """Fetch live market data for all Tadawul-listed instruments.

    Returns a dict keyed by ticker symbol:
        {
            "2222": {
                "ticker": "2222",
                "name_en": "SAUDI ARAMCO",
                "name_ar": "أرامكو السعودية",
                "price": 26.12,
                "volume": 7152648,
                "turnover": 187248593.04,
                "no_of_trades": 10700,
                "change": 0.0,
                "change_pct": 0.0,
                "avg_trade_size": 668.47,
                ...
            },
            ...
        }
    Returns cached/stale data on failure; None if no data available at all.
    """
    cache_key = "stock_prices"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        with _playwright_session() as page:
            raw = _fetch_servlet_json(page, "TickerServlet")
            if raw is None:
                logger.warning("Tadawul TickerServlet returned no data")
                return _get_stale(cache_key)

            stocks = raw.get("stockData", [])
            result: dict[str, dict] = {}
            for s in stocks:
                ticker = s.get("pk_rf_company", "")
                if not ticker:
                    continue
                result[ticker] = {
                    "ticker": ticker,
                    "name_en": s.get("companyShortNameEn", ""),
                    "name_ar": s.get("companyShortNameAr", ""),
                    "name_long_en": s.get("companyLongNameEn", ""),
                    "name_long_ar": s.get("companyLongNameAr", ""),
                    "price": s.get("lastTradePrice"),
                    "volume": s.get("volumeTraded"),
                    "turnover": s.get("turnOver"),
                    "no_of_trades": s.get("noOfTrades"),
                    "change": s.get("change"),
                    "change_pct": s.get("changePercent"),
                    "avg_trade_size": s.get("aveTradeSize"),
                    "high": s.get("highPrice"),
                    "low": s.get("lowPrice"),
                    "open": s.get("todaysOpen"),
                    "prev_close": s.get("previousClosePrice"),
                }

            _set_cache(cache_key, result)
            return result

    except Exception as e:
        logger.error(f"Tadawul get_all_stock_prices: {e}")
        return _get_stale(cache_key)


def get_stock_price(ticker: str) -> dict | None:
    """Fetch live market data for a single ticker."""
    all_prices = get_all_stock_prices()
    if all_prices is None:
        return None
    stock = all_prices.get(ticker.strip())
    if stock is None:
        return None
    # Propagate cached/stale flags from the batch result
    if all_prices.get("cached"):
        stock = {**stock, "cached": True}
    if all_prices.get("stale"):
        stock = {**stock, "stale": True}
    return stock


def get_company_directory() -> list[dict] | None:
    """Fetch the full Tadawul company directory.

    Returns a list of company dicts:
        [
            {
                "symbol": "2222",
                "name_en": "Saudi Arabian Oil Co.",
                "name_ar": "شركة الزيت العربية السعودية",
                "trading_name_en": "SAUDI ARAMCO",
                "trading_name_ar": "أرامكو السعودية",
                "market_type": "M",  # M=Main, S=NomuC, B=Sukuk, D=Derivative, F=Fund
                "isin": "SA12A0540E19",
            },
            ...
        ]
    """
    cache_key = "company_directory"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        with _playwright_session() as page:
            raw = _fetch_servlet_json(page, "ThemeSearchUtilityServlet")
            if raw is None or not isinstance(raw, list):
                logger.warning("Tadawul ThemeSearchUtilityServlet returned no data")
                return _get_stale(cache_key)

            result = [
                {
                    "symbol": c.get("symbol", ""),
                    "name_en": c.get("companyNameEN", ""),
                    "name_ar": c.get("companyNameAR", ""),
                    "trading_name_en": c.get("tradingNameEn", ""),
                    "trading_name_ar": c.get("tradingNameAr", ""),
                    "market_type": c.get("market_type", ""),
                    "isin": c.get("isin", ""),
                }
                for c in raw
                if c.get("symbol")
            ]

            _set_cache(cache_key, result)
            return result

    except Exception as e:
        logger.error(f"Tadawul get_company_directory: {e}")
        return _get_stale(cache_key)


def get_market_summary() -> dict | None:
    """Fetch Tadawul market summary (indices, advancers/decliners, market status).

    Returns:
        {
            "tasi": {"value": 10856.90, "change": 56.98, "change_pct": 0.53, ...},
            "mt30": {"value": 1442.66, "change": 6.23, ...},
            "nomuc": {"value": 22912.40, "change": -138.7, ...},
            "sukuk_index": {"value": 914.44, ...},
            "market_status": "CLOSED",  # or OPEN, PRE_OPEN, etc.
            "advancers": 176,
            "decliners": 83,
            "unchanged": 11,
            "volume_traded": 294132853,
            "turnover": 5000874221.84,
            "no_of_trades": 455638,
            "no_of_companies_traded": 267,
            "timestamp": "...",
            "source": "Saudi Exchange (Tadawul)",
        }
    """
    cache_key = "market_summary"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        with _playwright_session() as page:
            raw = _fetch_servlet_json(page, "ThemeTASIUtilityServlet")
            if raw is None:
                logger.warning("Tadawul ThemeTASIUtilityServlet returned no data")
                return _get_stale(cache_key)

            # Market status codes: 0=Closed, 1=Pre-Open, 2=Open, 3=Closed(Auction)
            market_status_map = {0: "CLOSED", 1: "PRE_OPEN", 2: "OPEN", 3: "CLOSED"}
            msc = raw.get("marketStatusCode", 0)

            mb = raw.get("marketBean", {})

            def _idx(val_key: str, change_key: str, pct_key: str,
                     status_key: str, bean_key: str, summary_key: str,
                     ytd_key: str, wk52_key: str) -> dict:
                bean = raw.get(bean_key, {})
                summary = bean.get(summary_key, {})
                ytd = bean.get(ytd_key, {})
                wk52 = bean.get(wk52_key, {})
                return {
                    "value": _parse_num(raw.get(val_key)),
                    "change": _parse_num(raw.get(change_key)),
                    "change_pct": _parse_num(raw.get(pct_key)),
                    "open": _parse_num(summary.get("openPrice")),
                    "high": _parse_num(summary.get("highPrice")),
                    "low": _parse_num(summary.get("lowPrice")),
                    "volume": summary.get("volumeTraded"),
                    "turnover": summary.get("turnOver"),
                    "no_of_trades": summary.get("noOfTrades"),
                    "prev_close": _parse_num(summary.get("previouseIndexPrice")),
                    "week_52_high": wk52.get("maxPrice"),
                    "week_52_low": wk52.get("minPrice"),
                    "ytd_change": ytd.get("change"),
                    "ytd_change_pct": ytd.get("percentChange"),
                    "status": market_status_map.get(
                        raw.get(status_key, 0), "UNKNOWN"
                    ),
                }

            result = {
                "tasi": _idx(
                    "tasiValue", "tasiNetChange", "tasiPercentageChange", "tasiStatus",
                    "tasiBean", "tasiTodaysSummaryBean",
                    "tasiYearToDateBean", "tasi52WeeksBean",
                ),
                "mt30": _idx(
                    "mt30IndexValue", "mt30IndexNetChange", "mt30IndexPercentageChange",
                    "mt30Status",
                    "mt30Bean", "tasiTodaysSummaryBean",
                    "tasiYearToDateBean", "tasi52WeeksBean",
                ),
                "nomuc": _idx(
                    "smeSasiValue", "smeSasiNetChange", "smeSasiPercentageChange",
                    "smeSasiStatus",
                    "smeSasiBean", "smeSasITodaysSummaryBean",
                    "smeSASIYearToDateBean", "smeSASI52WeeksBean",
                ),
                "sukuk_index": _idx(
                    "sukukValue", "sukukNetChange", "sukukPercentageChange", "sukukStatus",
                    "sukukIndicesBean", "tasiTodaysSummaryBean",
                    "tasiYearToDateBean", "tasi52WeeksBean",
                ),
                "market_status": market_status_map.get(msc, "UNKNOWN"),
                "market_status_code": msc,
                "advancers": mb.get("noOfUps"),
                "decliners": mb.get("noOfDowns"),
                "unchanged": mb.get("noOfNoChanges"),
                "volume_traded": mb.get("volumeTraded"),
                "turnover": mb.get("turnover"),
                "no_of_trades": mb.get("noOfTrades"),
                "no_of_companies_traded": mb.get("noOfSymbolsTraded"),
                "current_time": raw.get("currentTime"),
                "timestamp": int(time.time()),
                "source": "Saudi Exchange (Tadawul)",
                "cached": False,
            }

            _set_cache(cache_key, result)
            return result

    except Exception as e:
        logger.error(f"Tadawul get_market_summary: {e}")
        return _get_stale(cache_key)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_num(val: Any) -> float | None:
    """Parse a value that might be a string like '10,856.90' into float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _fmt(val: Any, fmt_spec: str = "+.2f") -> str:
    """Format a number for display, handling None gracefully."""
    if val is None:
        return "N/A"
    try:
        return format(val, fmt_spec)
    except (ValueError, TypeError):
        return str(val)


# ── CLI for testing ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    print("\n1. Market Summary")
    print("=" * 60)
    summary = get_market_summary()
    if summary:
        tasi = summary["tasi"]
        print(f"  TASI: {tasi['value']} ({_fmt(tasi['change'])}, {_fmt(tasi['change_pct'])}%)")
        mt30 = summary["mt30"]
        print(f"  MT30: {mt30['value']} ({_fmt(mt30['change'])}, {_fmt(mt30['change_pct'])}%)")
        print(f"  Market: {summary['market_status']}")
        print(f"  Advancers: {summary['advancers']}, Decliners: {summary['decliners']}")
        vol = summary['volume_traded'] or 0
        turn = summary['turnover'] or 0
        print(f"  Volume: {vol:,}, Turnover: {turn:,.0f}")

    print("\n2. Stock Prices (sample)")
    print("=" * 60)
    prices = get_all_stock_prices()
    if prices:
        print(f"  Total instruments: {len(prices)}")
        for ticker in ("2222", "1180", "1120", "2010"):
            s = prices.get(ticker)
            if s:
                price = s['price']
                vol = s['volume'] or 0
                print(f"  {ticker} ({s['name_en']}): {price} SAR, Vol: {vol:,}")

    print("\n3. Company Directory")
    print("=" * 60)
    companies = get_company_directory()
    if companies:
        print(f"  Total companies: {len(companies)}")
        # Count by market type
        types: dict[str, int] = {}
        for c in companies:
            mt = c["market_type"]
            types[mt] = types.get(mt, 0) + 1
        type_names = {"M": "Main", "S": "NomuC", "B": "Sukuk", "D": "Derivative", "F": "Fund", "C": "C?", "E": "E?", "O": "O?"}
        for mt, count in sorted(types.items()):
            print(f"  {type_names.get(mt, mt)}: {count}")
