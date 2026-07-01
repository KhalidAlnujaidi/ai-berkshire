"""Tests for portfolio endpoints.

Covers: add holding, weighted-average on duplicate, update, delete,
list with enrichment, and auth guards.
"""
import sys
import os
from pathlib import Path

# Ensure backend dir is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from database import engine, SessionLocal, Base
from models import User, Holding

# Use test database
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ["JWT_SECRET_KEY"] = "x" * 64  # bypass production guard

from app import app

client = TestClient(app)


_test_counter = [0]

def _setup_db():
    """Create tables and return a fresh test user with a token."""
    _test_counter[0] += 1
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        app.state.limiter.reset()
    except Exception:
        pass
    db = SessionLocal()

    # Register a user via the API
    resp = client.post("/api/auth/register", json={
        "email": f"portfoliotest_{_test_counter[0]}@test.com",
        "password": "testpassword123",
    })
    token = resp.json()["access_token"]
    db.close()
    return token


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Tests ────────────────────────────────────────────────────────────────────

def test_add_holding():
    """Add a stock holding to the portfolio."""
    token = _setup_db()
    resp = client.post("/api/portfolio", json={
        "ticker": "1120",
        "name_en": "Al Rajhi Bank",
        "name_ar": "مصرف الراجحي",
        "sector_en": "Islamic Banking",
        "quantity": 100,
        "buy_price": 60.0,
    }, headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "1120"
    assert data["quantity"] == 100
    assert data["buy_price"] == 60.0


def test_add_duplicate_holding_averages_price():
    """Adding the same ticker again should average the buy price."""
    token = _setup_db()
    # First buy: 100 @ 60
    client.post("/api/portfolio", json={
        "ticker": "1120", "quantity": 100, "buy_price": 60.0,
    }, headers=_auth_headers(token))
    # Second buy: 100 @ 70 → avg = 65
    resp = client.post("/api/portfolio", json={
        "ticker": "1120", "quantity": 100, "buy_price": 70.0,
    }, headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == 200
    assert data["buy_price"] == 65.0


def test_get_portfolio():
    """Get portfolio summary with holdings."""
    token = _setup_db()
    client.post("/api/portfolio", json={
        "ticker": "1120", "quantity": 100, "buy_price": 60.0,
    }, headers=_auth_headers(token))
    client.post("/api/portfolio", json={
        "ticker": "2222", "quantity": 50, "buy_price": 30.0,
    }, headers=_auth_headers(token))

    resp = client.get("/api/portfolio", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_holdings"] == 2
    assert data["total_cost"] == 7500.0  # 100*60 + 50*30


def test_update_holding():
    """Update a holding's quantity."""
    token = _setup_db()
    client.post("/api/portfolio", json={
        "ticker": "1120", "quantity": 100, "buy_price": 60.0,
    }, headers=_auth_headers(token))

    resp = client.put("/api/portfolio/1120", json={
        "quantity": 150,
    }, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 150


def test_delete_holding():
    """Delete a holding from the portfolio."""
    token = _setup_db()
    client.post("/api/portfolio", json={
        "ticker": "1120", "quantity": 100, "buy_price": 60.0,
    }, headers=_auth_headers(token))

    resp = client.delete("/api/portfolio/1120", headers=_auth_headers(token))
    assert resp.status_code == 200

    # Verify it's gone
    resp = client.get("/api/portfolio", headers=_auth_headers(token))
    assert resp.json()["total_holdings"] == 0


def test_portfolio_requires_auth():
    """Portfolio endpoints should require authentication."""
    resp = client.get("/api/portfolio")
    assert resp.status_code == 401


def test_update_nonexistent_holding():
    """Updating a non-existent holding returns 404."""
    token = _setup_db()
    resp = client.put("/api/portfolio/9999", json={
        "quantity": 100,
    }, headers=_auth_headers(token))
    assert resp.status_code == 404


def test_delete_nonexistent_holding():
    """Deleting a non-existent holding returns 404."""
    token = _setup_db()
    resp = client.delete("/api/portfolio/9999", headers=_auth_headers(token))
    assert resp.status_code == 404


def test_empty_portfolio():
    """Empty portfolio returns zeros."""
    token = _setup_db()
    resp = client.get("/api/portfolio", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_holdings"] == 0
    assert data["total_cost"] == 0
    assert data["total_value"] == 0


if __name__ == "__main__":
    tests = [
        test_add_holding, test_add_duplicate_holding_averages_price,
        test_get_portfolio, test_update_holding, test_delete_holding,
        test_portfolio_requires_auth, test_update_nonexistent_holding,
        test_delete_nonexistent_holding, test_empty_portfolio,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} portfolio tests passed")
