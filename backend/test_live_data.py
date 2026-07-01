#!/usr/bin/env python3
"""
Tests for live stock price endpoints and Prometheus metrics.

Tests the new endpoints:
  - GET  /api/stocks/{ticker}/price
  - GET  /api/prices
  - POST /api/prices/refresh
  - GET  /metrics  (Prometheus)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)


# ── Metrics endpoint ─────────────────────────────────────────────────────────

r = client.get('/metrics')
print(f"METRICS: {r.status_code}")
assert r.status_code == 200
assert 'mizan_http_requests_total' in r.text or 'mizan' in r.text.lower()
print(f"  Prometheus format OK ({len(r.text)} bytes)")


# ── Price refresh (cache clear) ──────────────────────────────────────────────

r = client.post('/api/prices/refresh')
print(f"PRICE REFRESH (all): {r.status_code}")
assert r.status_code == 200
assert 'Cache cleared' in r.json().get('message', '')

r = client.post('/api/prices/refresh?ticker=1120')
print(f"PRICE REFRESH (single): {r.status_code}")
assert r.status_code == 200
assert '1120' in r.json().get('message', '')


# ── Single stock price ──────────────────────────────────────────────────────

# Test 404 for nonexistent ticker
r = client.get('/api/stocks/FAKE/price')
print(f"PRICE (fake ticker): {r.status_code}")
assert r.status_code == 404

# Test a real ticker — this will attempt Yahoo Finance.
# If Yahoo is unreachable (CI/no network), we expect either:
#   200 with cached/fresh data, or
#   503 if no data available at all
r = client.get('/api/stocks/1120/price')
print(f"PRICE (1120 Al Rajhi): {r.status_code}")
if r.status_code == 200:
    body = r.json()
    assert body['ticker'] == '1120'
    assert 'name_ar' in body
    assert body['name_ar'] == 'مصرف الراجحي'
    assert 'price' in body
    assert 'source' in body
    assert 'cached' in body
    print(f"  Price: {body.get('price')} {body.get('currency', 'SAR')}")
    print(f"  Day change: {body.get('day_change')} ({body.get('day_change_pct')}%)")
    print(f"  Source: {body.get('source')}, Cached: {body.get('cached')}")
elif r.status_code == 503:
    print(f"  Yahoo Finance unreachable in this environment — 503 is acceptable (fail-soft)")
else:
    raise AssertionError(f"Unexpected status {r.status_code}: {r.text}")


# ── Bulk prices ─────────────────────────────────────────────────────────────

r = client.get('/api/prices?tickers=1120,2222')
print(f"BULK PRICES (2 tickers): {r.status_code}")
assert r.status_code == 200
body = r.json()
assert body['requested'] == 2
print(f"  Requested: {body['requested']}, Received: {body['count']}")
# count might be < requested if Yahoo is down — that's fine (fail-soft)

# Test bulk with no tickers (should default to all halal stocks)
r = client.get('/api/prices')
print(f"BULK PRICES (all halal): {r.status_code}")
assert r.status_code == 200
body = r.json()
assert body['requested'] >= 14  # we have 14 halal stocks
print(f"  Requested: {body['requested']}, Received: {body['count']}")


# ── Metrics after requests ──────────────────────────────────────────────────

r = client.get('/metrics')
assert r.status_code == 200
# Should have recorded our test requests
assert 'mizan_http_requests_total' in r.text
print(f"METRICS (after requests): {r.status_code} — metrics recorded")


# ── Existing endpoints still work ───────────────────────────────────────────

r = client.get('/api/health')
assert r.status_code == 200
assert r.json()['stocks_count'] >= 49
print(f"HEALTH: {r.status_code} — {r.json()['stocks_count']} stocks")

r = client.get('/api/stocks/1120')
assert r.status_code == 200
assert 'COMPLIANT' in r.json()['verdict']
print(f"STOCK 1120: {r.status_code} — {r.json()['verdict']}")

r = client.get('/api/halal-stocks')
assert r.status_code == 200
assert r.json()['count'] >= 14
print(f"HALAL STOCKS: {r.status_code} — {r.json()['count']} halal")


print("\n✅✅ All price + metrics tests passed!")
