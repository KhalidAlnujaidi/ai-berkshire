"""Tests for the 5 Tadawul API endpoints.

These tests exercise the FastAPI routing layer of the Tadawul endpoints
WITHOUT touching the real saudiexchange.sa site (which requires a Playwright
browser + Akamai bypass). The scraper functions are monkeypatched to return
deterministic fixture data, so the tests run fast and offline.

What is covered:
  - GET  /api/tadawul/prices            (all prices, ticker filter, halal_only filter)
  - GET  /api/tadawul/prices/{ticker}   (single price, 404 on unknown)
  - GET  /api/tadawul/summary           (market summary, 503 when unavailable)
  - GET  /api/tadawul/companies         (directory, market_type + search filters)
  - POST /api/tadawul/cache/refresh     (cache clear)

What is NOT covered here (deliberately):
  - The Playwright scraping itself — that is an integration concern and is
    tested by tadawul_scraper.py's __main__ block against the live site.
  - Rate limiting thresholds (slowapi) — those are infra, not behavior.

Run:
    cd ai-berkshire/backend && .venv/bin/pytest test_tadawul.py -v
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
sys.path.insert(0, os.path.dirname(__file__))

# Ensure the app doesn't write to a real DB during these endpoint tests.
# The Tadawul endpoints don't touch the DB, but import-time side effects
# (init_db on startup) would. We use an in-memory SQLite DB to stay isolated.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_tadawul_ep.db")

from fastapi.testclient import TestClient  # noqa: E402

import tadawul_scraper  # noqa: E402
from app import app  # noqa: E402

client = TestClient(app)


# ── Fixtures (plain dicts, mimicking real scraper output shape) ─────────────

FIXTURE_PRICES = {
    "2222": {
        "ticker": "2222",
        "name_en": "SAUDI ARAMCO",
        "name_ar": "أرامكو السعودية",
        "price": 26.12,
        "volume": 7152648,
        "turnover": 187248593.04,
        "no_of_trades": 10700,
        "change": 0.10,
        "change_pct": 0.38,
        "cached": False,
    },
    "1120": {
        "ticker": "1120",
        "name_en": "AL RAJHI BANK",
        "name_ar": "بنك الراجحي",
        "price": 78.50,
        "volume": 3120000,
        "turnover": 244920000.0,
        "no_of_trades": 4100,
        "change": -0.20,
        "change_pct": -0.25,
        "cached": False,
    },
    "1180": {
        "ticker": "1180",
        "name_en": "SAUDI NATIONAL BANK",
        "name_ar": "البنك الأهلي السعودي",
        "price": 31.40,
        "volume": 5600000,
        "turnover": 175840000.0,
        "no_of_trades": 8200,
        "change": 0.05,
        "change_pct": 0.16,
        "cached": False,
    },
}

FIXTURE_SUMMARY = {
    "tasi": {"value": 10856.90, "change": 56.98, "change_pct": 0.53, "status": "CLOSED"},
    "mt30": {"value": 1442.66, "change": 6.23, "change_pct": 0.43, "status": "CLOSED"},
    "nomuc": {"value": 22912.40, "change": -138.7, "change_pct": -0.60, "status": "CLOSED"},
    "sukuk_index": {"value": 914.44, "change": 0.0, "change_pct": 0.0, "status": "CLOSED"},
    "market_status": "CLOSED",
    "market_status_code": 0,
    "advancers": 176,
    "decliners": 83,
    "unchanged": 11,
    "volume_traded": 294132853,
    "turnover": 5000874221.84,
    "no_of_trades": 455638,
    "no_of_companies_traded": 267,
    "current_time": None,
    "timestamp": int(time.time()),
    "source": "Saudi Exchange (Tadawul)",
    "cached": False,
}

FIXTURE_COMPANIES = [
    {"symbol": "2222", "name_en": "Saudi Aramco", "name_ar": "أرامكو السعودية",
     "trading_name_en": "ARAMCO", "trading_name_ar": "أرامكو", "market_type": "M",
     "isin": "SA0007879542"},
    {"symbol": "1120", "name_en": "Al Rajhi Bank", "name_ar": "بنك الراجحي",
     "trading_name_en": "ALRAJHI", "trading_name_ar": "الراجحي", "market_type": "M",
     "isin": "SA000AIN0057"},
    {"symbol": "2040", "name_en": "Saudi Telecom", "name_ar": "مجموعة الاتصالات السعودية",
     "trading_name_en": "STC", "trading_name_ar": "إس تي سي", "market_type": "M",
     "isin": "SA000H2G322"},
    {"symbol": "9999", "name_en": "NomuC Example Co", "name_ar": "شركة نمو نمو",
     "trading_name_en": "NOMUC1", "trading_name_ar": "نمو1", "market_type": "S",
     "isin": "SA00FAKE0001"},
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _patch_all(monkeypatch):
    """Monkeypatch the 4 scraper functions used by the endpoints."""
    monkeypatch.setattr(tadawul_scraper, "get_all_stock_prices", lambda: FIXTURE_PRICES)
    monkeypatch.setattr(tadawul_scraper, "get_stock_price",
                        lambda t: FIXTURE_PRICES.get(t))
    monkeypatch.setattr(tadawul_scraper, "get_market_summary", lambda: FIXTURE_SUMMARY)
    monkeypatch.setattr(tadawul_scraper, "get_company_directory", lambda: FIXTURE_COMPANIES)


# ── GET /api/tadawul/prices ──────────────────────────────────────────────────

def test_all_prices_returns_list(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/prices")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(FIXTURE_PRICES)
    assert body["count"] == len(body["prices"])
    tickers = [p["ticker"] for p in body["prices"]]
    assert "2222" in tickers
    assert "1120" in tickers


def test_all_prices_ticker_filter(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/prices?ticker=2222")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert body["prices"][0]["ticker"] == "2222"
    assert body["prices"][0]["name_en"] == "SAUDI ARAMCO"


def test_all_prices_ticker_filter_404(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/prices?ticker=NOPE")
    assert r.status_code == 404


def test_all_prices_503_when_unavailable(monkeypatch):
    monkeypatch.setattr(tadawul_scraper, "get_all_stock_prices", lambda: None)
    r = client.get("/api/tadawul/prices")
    assert r.status_code == 503


def test_all_prices_halal_only_filter(monkeypatch):
    """halal_only filters to Sharia-compliant tickers from stocks.json."""
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/prices?halal_only=true")
    assert r.status_code == 200
    body = r.json()
    # Al Rajhi (1120) is compliant; SNB (1180) is not. Aramco (2222) is compliant.
    tickers = [p["ticker"] for p in body["prices"]]
    assert "1120" in tickers          # compliant — present
    assert "1180" not in tickers      # non-compliant — filtered out


# ── GET /api/tadawul/prices/{ticker} ─────────────────────────────────────────

def test_single_price_ok(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/prices/1120")
    assert r.status_code == 200
    assert r.json()["ticker"] == "1120"
    assert r.json()["price"] == 78.50


def test_single_price_404(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/prices/FAKE")
    assert r.status_code == 404


def test_single_price_404_when_unavailable(monkeypatch):
    monkeypatch.setattr(tadawul_scraper, "get_stock_price", lambda t: None)
    r = client.get("/api/tadawul/prices/1120")
    assert r.status_code == 404


# ── GET /api/tadawul/summary ─────────────────────────────────────────────────

def test_market_summary_ok(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["tasi"]["value"] == 10856.90
    assert body["market_status"] == "CLOSED"
    assert body["advancers"] == 176
    assert body["decliners"] == 83


def test_market_summary_503_when_unavailable(monkeypatch):
    monkeypatch.setattr(tadawul_scraper, "get_market_summary", lambda: None)
    r = client.get("/api/tadawul/summary")
    assert r.status_code == 503


# ── GET /api/tadawul/companies ───────────────────────────────────────────────

def test_companies_all(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/companies")
    assert r.status_code == 200
    assert r.json()["count"] == len(FIXTURE_COMPANIES)


def test_companies_market_type_filter(monkeypatch):
    _patch_all(monkeypatch)
    r = client.get("/api/tadawul/companies?market_type=M")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert all(c["market_type"] == "M" for c in body["companies"])


def test_companies_search_filter(monkeypatch):
    _patch_all(monkeypatch)
    # English search
    r = client.get("/api/tadawul/companies?q=aramco")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert body["companies"][0]["symbol"] == "2222"

    # Arabic search
    r = client.get("/api/tadawul/companies?q=الراجحي")
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["companies"][0]["symbol"] == "1120"

    # Symbol search
    r = client.get("/api/tadawul/companies?q=2222")
    assert r.status_code == 200
    assert r.json()["count"] == 1


def test_companies_503_when_unavailable(monkeypatch):
    monkeypatch.setattr(tadawul_scraper, "get_company_directory", lambda: None)
    r = client.get("/api/tadawul/companies")
    assert r.status_code == 503


# ── POST /api/tadawul/cache/refresh ──────────────────────────────────────────

def test_cache_refresh(monkeypatch):
    cleared = {"called": False}
    def _fake_clear(key=None):
        cleared["called"] = True
    monkeypatch.setattr(tadawul_scraper, "clear_cache", _fake_clear)
    r = client.post("/api/tadawul/cache/refresh")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert cleared["called"] is True


# ── Edge: rate-limit safety ──────────────────────────────────────────────────
# We do NOT hammer the endpoint to trigger 429 — slowapi config is infra.
# But we sanity-check that a single call works (covered above).
