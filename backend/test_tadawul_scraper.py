"""Tests for the Tadawul scraper module.

These tests require Playwright + xvfb (headed browser to bypass Akamai).
Run with:
    xvfb-run --auto-servernum python -m pytest test_tadawul_scraper.py -v --timeout=120

Note: Tests make real network calls to saudiexchange.sa. They are integration
tests, not unit tests. Each test opens a browser session (~6-8s), so the full
suite takes ~20-25s. Cache is shared across tests within a single session.
"""

import os
import sys
import time

import pytest

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tadawul_scraper import (
    get_all_stock_prices,
    get_company_directory,
    get_market_summary,
    get_stock_price,
    clear_cache,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_cache_before():
    """Start each test with a clean cache."""
    clear_cache()
    yield


# ── Market Summary Tests ────────────────────────────────────────────────────

class TestMarketSummary:
    def test_returns_dict(self):
        summary = get_market_summary()
        assert summary is not None, "Market summary should not be None"

    def test_has_tasi(self):
        summary = get_market_summary()
        assert "tasi" in summary
        tasi = summary["tasi"]
        assert tasi["value"] is not None
        assert isinstance(tasi["value"], (int, float))
        # TASI is currently around 10000-12000
        assert 5000 < tasi["value"] < 20000

    def test_has_market_status(self):
        summary = get_market_summary()
        assert "market_status" in summary
        assert summary["market_status"] in ("OPEN", "CLOSED", "PRE_OPEN", "UNKNOWN")

    def test_has_advancers_decliners(self):
        summary = get_market_summary()
        assert summary["advancers"] is not None
        assert summary["decliners"] is not None
        assert isinstance(summary["advancers"], int)
        assert isinstance(summary["decliners"], int)
        assert summary["advancers"] >= 0
        assert summary["decliners"] >= 0

    def test_has_source(self):
        summary = get_market_summary()
        assert summary["source"] == "Saudi Exchange (Tadawul)"

    def test_caching(self):
        """Second call should be instant (from cache)."""
        clear_cache()
        t0 = time.monotonic()
        get_market_summary()
        t_live = time.monotonic() - t0

        t0 = time.monotonic()
        get_market_summary()
        t_cached = time.monotonic() - t0

        assert t_cached < 0.01, f"Cached call took {t_cached:.3f}s, expected <0.01s"
        assert t_cached < t_live


# ── Stock Prices Tests ──────────────────────────────────────────────────────

class TestStockPrices:
    def test_returns_dict(self):
        prices = get_all_stock_prices()
        assert prices is not None, "Stock prices should not be None"

    def test_has_many_stocks(self):
        prices = get_all_stock_prices()
        # Tadawul has 270+ main market stocks, plus funds, sukuk, etc.
        assert len(prices) >= 200, f"Expected 200+ instruments, got {len(prices)}"

    def test_aramco_present(self):
        prices = get_all_stock_prices()
        assert "2222" in prices, "Aramco (2222) should be in price data"
        aramco = prices["2222"]
        assert aramco["name_en"] == "SAUDI ARAMCO"
        assert aramco["price"] is not None
        assert aramco["price"] > 0

    def test_alrajhi_present(self):
        prices = get_all_stock_prices()
        assert "1120" in prices, "Al Rajhi Bank (1120) should be in price data"
        stock = prices["1120"]
        assert stock["price"] is not None
        assert stock["price"] > 0

    def test_stock_has_required_fields(self):
        prices = get_all_stock_prices()
        aramco = prices["2222"]
        required_fields = [
            "ticker", "name_en", "name_ar", "price", "volume",
            "turnover", "no_of_trades", "change", "change_pct",
        ]
        for field in required_fields:
            assert field in aramco, f"Missing field: {field}"

    def test_single_stock_price(self):
        stock = get_stock_price("2222")
        assert stock is not None
        assert stock["ticker"] == "2222"
        assert stock["name_en"] == "SAUDI ARAMCO"

    def test_single_stock_cached_flag(self):
        """get_stock_price should propagate cached flag from batch."""
        get_all_stock_prices()  # Populate cache
        stock = get_stock_price("2222")
        assert stock is not None
        assert stock.get("cached") is True


# ── Company Directory Tests ─────────────────────────────────────────────────

class TestCompanyDirectory:
    def test_returns_list(self):
        companies = get_company_directory()
        assert companies is not None, "Company directory should not be None"
        assert isinstance(companies, list)

    def test_has_many_companies(self):
        companies = get_company_directory()
        assert len(companies) >= 500, f"Expected 500+ companies, got {len(companies)}"

    def test_aramco_in_directory(self):
        companies = get_company_directory()
        aramco = [c for c in companies if c["symbol"] == "2222"]
        assert len(aramco) == 1
        assert "Oil" in aramco[0]["name_en"] or "ARAMCO" in aramco[0]["trading_name_en"]
        assert aramco[0]["market_type"] == "M"  # Main market

    def test_company_has_required_fields(self):
        companies = get_company_directory()
        sample = companies[0]
        required_fields = [
            "symbol", "name_en", "name_ar",
            "market_type", "isin",
        ]
        for field in required_fields:
            assert field in sample, f"Missing field: {field}"

    def test_has_main_market_companies(self):
        companies = get_company_directory()
        main_market = [c for c in companies if c["market_type"] == "M"]
        assert len(main_market) >= 200, f"Expected 200+ main market, got {len(main_market)}"


# ── Fail-soft Tests ─────────────────────────────────────────────────────────

class TestFailSoft:
    def test_nonexistent_ticker(self):
        stock = get_stock_price("99999")
        assert stock is None
