"""Live stock price service for Saudi and US stocks.

Fetches real-time price data from Yahoo Finance's chart API (no auth needed).
Caches results with a TTL; fails soft by returning cached data when the API
is unreachable.

Design decisions:
- Yahoo Finance chart API is used (not quoteSummary) because it requires no
  crumb/cookie auth and is more reliable for simple price data.
- Saudi tickers on Yahoo use the suffix ".SR" (e.g., 1120.SR).
- US tickers (e.g., AAPL) are used without a suffix.
- Cache is in-memory with a monotonic clock — no external dependency.
- Fail-soft: if Yahoo is down, we serve stale cached data rather than erroring.
"""

import time
import logging
import urllib.request
import urllib.error
import json
from datetime import datetime, timezone
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 300  # 5 minutes — balance freshness vs Yahoo rate limits
REQUEST_TIMEOUT = 10     # seconds — fail fast if Yahoo is slow

# ── In-memory cache ──────────────────────────────────────────────────────────

_price_cache: dict[str, tuple[float, dict]] = {}  # ticker -> (timestamp, data)


def _now() -> float:
    """Monotonic clock — immune to system clock changes."""
    return time.monotonic()


def clear_cache(ticker: Optional[str] = None) -> None:
    """Clear the price cache. If ticker given, clear only that entry."""
    if ticker:
        _price_cache.pop(ticker, None)
    else:
        _price_cache.clear()


def get_cached(ticker: str) -> Optional[dict]:
    """Return cached price data if fresh, else None."""
    entry = _price_cache.get(ticker)
    if entry is None:
        return None
    ts, data = entry
    if _now() - ts > CACHE_TTL_SECONDS:
        return None
    return {**data, "cached": True}


def get_stale(ticker: str) -> Optional[dict]:
    """Return stale cached data even if expired (fail-soft fallback)."""
    entry = _price_cache.get(ticker)
    if entry is None:
        return None
    _, data = entry
    return {**data, "cached": True, "stale": True}


# ── Ticker helpers ───────────────────────────────────────────────────────────

def _is_saudi_ticker(ticker: str) -> bool:
    """Return True if ticker is a Saudi stock (purely numeric, e.g. 1120)."""
    return ticker.strip().isdigit()


def get_market(ticker: str) -> str:
    """Determine the market for a ticker.

    Saudi tickers are numeric (e.g., 1120).
    US tickers are alphabetic (e.g., AAPL).
    """
    if _is_saudi_ticker(ticker):
        return "saudi"
    return "us"


def _yahoo_symbol(ticker: str) -> str:
    """Convert a ticker to Yahoo Finance format.

    - Saudi stocks use '.SR' suffix (e.g., 1120 → 1120.SR)
    - US stocks are used as-is (e.g., AAPL → AAPL)
    - If already suffixed, leave as-is
    """
    ticker = ticker.strip()
    if "." in ticker:
        return ticker
    if _is_saudi_ticker(ticker):
        return f"{ticker}.SR"
    return ticker


# ── Yahoo Finance chart API ──────────────────────────────────────────────────

def _fetch_from_yahoo(ticker: str) -> Optional[dict]:
    """Fetch live price data from Yahoo Finance chart API.

    Returns None on any failure (network, parse, rate limit).
    """
    symbol = _yahoo_symbol(ticker)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.warning(f"Yahoo Finance: ticker {symbol} not found (404)")
        elif e.code == 429:
            logger.warning(f"Yahoo Finance: rate limited (429) for {symbol}")
        else:
            logger.warning(f"Yahoo Finance: HTTP {e.code} for {symbol}")
        return None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        logger.warning(f"Yahoo Finance: network error for {symbol}: {e}")
        return None
    except json.JSONDecodeError:
        logger.warning(f"Yahoo Finance: invalid JSON for {symbol}")
        return None

    # Parse the response
    try:
        result = payload.get("chart", {}).get("result")
        if not result:
            err = payload.get("chart", {}).get("error", {})
            logger.warning(f"Yahoo Finance: no result for {symbol}: {err.get('description', '?')}")
            return None

        meta = result[0]["meta"]
        indicators = result[0]["indicators"]["quote"][0]

        current_price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        currency = meta.get("currency", "SAR")
        exchange = meta.get("exchangeName", "Saudi")
        market_state = meta.get("marketState", "UNKNOWN")

        # Day change
        day_change = None
        day_change_pct = None
        if current_price is not None and prev_close is not None and prev_close > 0:
            day_change = round(current_price - prev_close, 2)
            day_change_pct = round((day_change / prev_close) * 100, 2)

        # Extract recent volume (latest non-null)
        volumes = indicators.get("volume", [])
        volume = None
        for v in reversed(volumes):
            if v is not None:
                volume = v
                break

        # 52-week range (from meta if available, else from data)
        fifty_two_week_low = meta.get("fiftyTwoWeekLow")
        fifty_two_week_high = meta.get("fiftyTwoWeekHigh")

        data = {
            "ticker": ticker,
            "price": current_price,
            "previous_close": prev_close,
            "day_change": day_change,
            "day_change_pct": day_change_pct,
            "currency": currency,
            "exchange": exchange,
            "market_state": market_state,
            "volume": volume,
            "fifty_two_week_low": fifty_two_week_low,
            "fifty_two_week_high": fifty_two_week_high,
            "timestamp": int(time.time()),
            "source": "Yahoo Finance",
            "cached": False,
        }

        # Cache it
        _price_cache[ticker] = (_now(), data)
        return data

    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Yahoo Finance: parse error for {symbol}: {e}")
        return None


# ── Price history (for charts) ───────────────────────────────────────────────

# Range → (yahoo range param, yahoo interval param)
_RANGE_MAP = {
    "1mo": ("1mo", "1d"),
    "3mo": ("3mo", "1d"),
    "6mo": ("6mo", "1wk"),
    "1y":  ("1y",  "1wk"),
}


def get_price_history(ticker: str, range: str = "1mo") -> Optional[list[dict]]:
    """Fetch historical price data from Yahoo Finance.

    Returns a list of {"date": "YYYY-MM-DD", "close": float, "volume": int|None}.
    Returns None on failure.
    """
    if range not in _RANGE_MAP:
        range = "1mo"
    y_range, y_interval = _RANGE_MAP[range]

    symbol = _yahoo_symbol(ticker)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?interval={y_interval}&range={y_range}"
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        logger.warning(f"Yahoo Finance history: HTTP {e.code} for {symbol}")
        return None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        logger.warning(f"Yahoo Finance history: error for {symbol}: {e}")
        return None

    try:
        result = payload.get("chart", {}).get("result")
        if not result:
            return None

        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
        closes = indicators.get("close", [])
        volumes = indicators.get("volume", [])

        history = []
        for i, ts in enumerate(timestamps):
            close = closes[i] if i < len(closes) else None
            if close is None:
                continue
            vol = volumes[i] if i < len(volumes) else None
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            history.append({
                "date": date_str,
                "close": round(close, 2),
                "volume": int(vol) if vol is not None else None,
            })

        return history if history else None

    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Yahoo Finance history: parse error for {symbol}: {e}")
        return None


# ── Public API ───────────────────────────────────────────────────────────────

def get_price(ticker: str) -> Optional[dict]:
    """Get live price for a single ticker.

    Returns cached data if fresh; otherwise fetches from Yahoo.
    Falls back to stale cache if Yahoo is unreachable.
    """
    ticker = ticker.strip()

    # Check fresh cache first
    cached = get_cached(ticker)
    if cached is not None:
        return cached

    # Fetch fresh data
    fresh = _fetch_from_yahoo(ticker)
    if fresh is not None:
        return fresh

    # Fail-soft: return stale data if we have it
    stale = get_stale(ticker)
    if stale is not None:
        logger.info(f"Serving stale price data for {ticker} (Yahoo unreachable)")
        return stale

    logger.warning(f"No price data available for {ticker}")
    return None


def get_prices_bulk(tickers: list[str]) -> dict[str, dict]:
    """Get prices for multiple tickers.

    Fetches sequentially with a small delay to avoid rate limiting.
    Returns a dict of ticker -> price_data. Tickers that fail are omitted.
    """
    results = {}
    for i, ticker in enumerate(tickers):
        data = get_price(ticker)
        if data is not None:
            results[ticker] = data
        # Small delay between requests to be respectful to Yahoo's API
        if i > 0 and i % 5 == 0:
            time.sleep(0.5)
    return results
