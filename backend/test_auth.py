"""Tests for the authentication and watchlist endpoints.

Run: cd backend && python test_auth.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.insert(0, os.path.dirname(__file__))

# Use a test database (in-memory SQLite)
os.environ["DATABASE_URL"] = "sqlite:///./test_mizan.db"

# Remove any stale test DB
test_db = os.path.join(os.path.dirname(__file__), "test_mizan.db")
if os.path.exists(test_db):
    os.remove(test_db)

from database import engine, Base, SessionLocal
import models  # register models
Base.metadata.create_all(bind=engine)

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)


# ── Auth Tests ──────────────────────────────────────────────────────────────

# Test register
r = client.post("/api/auth/register", json={
    "email": "test@mizan.dev",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "phone": "+966500000000",
})
print(f"REGISTER: {r.status_code}")
assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
data = r.json()
assert "access_token" in data
assert data["token_type"] == "bearer"
assert data["user"]["email"] == "test@mizan.dev"
assert data["user"]["full_name"] == "Test User"
print(f"  User ID: {data['user']['id']}, Email: {data['user']['email']}")
token = data["access_token"]

# Test duplicate email
r = client.post("/api/auth/register", json={
    "email": "test@mizan.dev",
    "password": "AnotherPass123!",
})
print(f"DUPLICATE EMAIL: {r.status_code}")
assert r.status_code == 409

# Test short password
r = client.post("/api/auth/register", json={
    "email": "short@mizan.dev",
    "password": "short",
})
print(f"SHORT PASSWORD: {r.status_code}")
assert r.status_code == 422  # Pydantic validation

# Test login
r = client.post("/api/auth/login", json={
    "email": "test@mizan.dev",
    "password": "SecurePass123!",
})
print(f"LOGIN: {r.status_code}")
assert r.status_code == 200
login_data = r.json()
assert "access_token" in login_data
assert login_data["user"]["email"] == "test@mizan.dev"
print(f"  Token received (first 20 chars): {login_data['access_token'][:20]}...")

# Test wrong password
r = client.post("/api/auth/login", json={
    "email": "test@mizan.dev",
    "password": "WrongPassword123!",
})
print(f"WRONG PASSWORD: {r.status_code}")
assert r.status_code == 401

# Test non-existent email
r = client.post("/api/auth/login", json={
    "email": "nobody@mizan.dev",
    "password": "SomePassword123!",
})
print(f"NON-EXISTENT EMAIL: {r.status_code}")
assert r.status_code == 401

# Test /api/auth/me with valid token
r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
print(f"ME: {r.status_code}")
assert r.status_code == 200
assert r.json()["email"] == "test@mizan.dev"

# Test /api/auth/me without token
r = client.get("/api/auth/me")
print(f"ME NO TOKEN: {r.status_code}")
assert r.status_code == 401

# Test /api/auth/me with invalid token
r = client.get("/api/auth/me", headers={"Authorization": "Bearer fake.token.here"})
print(f"ME INVALID TOKEN: {r.status_code}")
assert r.status_code == 401


# ── Watchlist Tests ─────────────────────────────────────────────────────────

auth_headers = {"Authorization": f"Bearer {token}"}

# Add to watchlist
r = client.post("/api/watchlist", json={
    "ticker": "1120",
    "name_en": "Al Rajhi Bank",
    "name_ar": "بنك الراجحي",
    "sector_en": "Banking",
    "sector_ar": "البنوك",
    "verdict": "COMPLIANT",
}, headers=auth_headers)
print(f"\nWATCHLIST ADD: {r.status_code}")
assert r.status_code == 200
assert r.json()["ticker"] == "1120"

# Add another
r = client.post("/api/watchlist", json={
    "ticker": "2222",
    "name_en": "Saudi Aramco",
    "name_ar": "أرامكو السعودية",
    "sector_en": "Energy",
    "sector_ar": "الطاقة",
    "verdict": "COMPLIANT",
}, headers=auth_headers)
assert r.status_code == 200

# Add duplicate (should be idempotent — return existing)
r = client.post("/api/watchlist", json={
    "ticker": "1120",
    "name_en": "Al Rajhi Bank",
}, headers=auth_headers)
print(f"DUPLICATE ADD: {r.status_code}")
assert r.status_code == 200

# Get watchlist
r = client.get("/api/watchlist", headers=auth_headers)
print(f"WATCHLIST GET: {r.status_code}, {len(r.json())} items")
assert r.status_code == 200
assert len(r.json()) == 2  # only 2 unique tickers
tickers = [item["ticker"] for item in r.json()]
assert "1120" in tickers
assert "2222" in tickers

# Remove from watchlist
r = client.delete("/api/watchlist/1120", headers=auth_headers)
print(f"WATCHLIST REMOVE: {r.status_code}")
assert r.status_code == 200

# Verify it's gone
r = client.get("/api/watchlist", headers=auth_headers)
assert len(r.json()) == 1
assert r.json()[0]["ticker"] == "2222"

# Remove non-existent (should 404)
r = client.delete("/api/watchlist/9999", headers=auth_headers)
print(f"REMOVE NON-EXISTENT: {r.status_code}")
assert r.status_code == 404

# Watchlist without auth (should 401)
r = client.get("/api/watchlist")
print(f"WATCHLIST NO AUTH: {r.status_code}")
assert r.status_code == 401


# ── Existing stock endpoints still work ─────────────────────────────────────

r = client.get("/api/health")
print(f"\nHEALTH: {r.status_code}, auth={r.json().get('auth')}")
assert r.status_code == 200
assert r.json()["auth"] == "enabled"

r = client.get("/api/stocks/1120")
print(f"STOCK LOOKUP: {r.status_code}, verdict={r.json().get('verdict')}")
assert r.status_code == 200

# Cleanup test DB
import os
if os.path.exists(test_db):
    os.remove(test_db)

print("\n✅✅ All auth + watchlist tests passed!")
