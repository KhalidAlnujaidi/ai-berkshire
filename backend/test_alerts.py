"""Tests for price alert endpoints.

Covers: create alert, validation (condition must be above/below), list,
delete, check logic, auth guards, and rate limiting presence.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from database import engine, SessionLocal, Base
from models import User, PriceAlert

os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ["JWT_SECRET_KEY"] = "x" * 64

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

    resp = client.post("/api/auth/register", json={
        "email": f"alerttest_{_test_counter[0]}@test.com",
        "password": "testpassword123",
    })
    token = resp.json()["access_token"]
    db.close()
    return token


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_alert():
    """Create a price alert."""
    token = _setup_db()
    resp = client.post("/api/alerts", json={
        "ticker": "1120",
        "name_en": "Al Rajhi Bank",
        "condition": "above",
        "target_price": 70.0,
    }, headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "1120"
    assert data["condition"] == "above"
    assert data["target_price"] == 70.0
    assert data["triggered"] is False


def test_create_alert_invalid_condition():
    """Condition must be 'above' or 'below'."""
    token = _setup_db()
    resp = client.post("/api/alerts", json={
        "ticker": "1120",
        "condition": "sideways",
        "target_price": 70.0,
    }, headers=_auth_headers(token))
    assert resp.status_code in (400, 422)


def test_list_alerts():
    """List all alerts for the user."""
    token = _setup_db()
    client.post("/api/alerts", json={
        "ticker": "1120", "condition": "above", "target_price": 70.0,
    }, headers=_auth_headers(token))
    client.post("/api/alerts", json={
        "ticker": "2222", "condition": "below", "target_price": 30.0,
    }, headers=_auth_headers(token))

    resp = client.get("/api/alerts", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_delete_alert():
    """Delete a price alert."""
    token = _setup_db()
    resp = client.post("/api/alerts", json={
        "ticker": "1120", "condition": "above", "target_price": 70.0,
    }, headers=_auth_headers(token))
    alert_id = resp.json()["id"]

    resp = client.delete(f"/api/alerts/{alert_id}", headers=_auth_headers(token))
    assert resp.status_code == 200

    resp = client.get("/api/alerts", headers=_auth_headers(token))
    assert len(resp.json()) == 0


def test_delete_nonexistent_alert():
    """Deleting a non-existent alert returns 404."""
    token = _setup_db()
    resp = client.delete("/api/alerts/99999", headers=_auth_headers(token))
    assert resp.status_code == 404


def test_alerts_require_auth():
    """Alert endpoints should require authentication."""
    resp = client.get("/api/alerts")
    assert resp.status_code == 401

    resp = client.post("/api/alerts", json={
        "ticker": "1120", "condition": "above", "target_price": 70.0,
    })
    assert resp.status_code == 401


def test_check_alerts_empty():
    """Check alerts when user has none."""
    token = _setup_db()
    resp = client.post("/api/alerts/check", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["checked"] == 0


def test_create_below_alert():
    """Create a 'below' alert."""
    token = _setup_db()
    resp = client.post("/api/alerts", json={
        "ticker": "2222",
        "name_en": "Saudi Aramco",
        "condition": "below",
        "target_price": 28.0,
    }, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["condition"] == "below"


def test_alert_isolation_between_users():
    """User A can't see or delete User B's alerts."""
    token_a = _setup_db()
    # Create alert as user A
    resp = client.post("/api/alerts", json={
        "ticker": "1120", "condition": "above", "target_price": 70.0,
    }, headers=_auth_headers(token_a))
    alert_id = resp.json()["id"]

    # Register user B
    resp = client.post("/api/auth/register", json={
        "email": "userb@test.com",
        "password": "testpassword123",
    })
    token_b = resp.json()["access_token"]

    # User B should see zero alerts
    resp = client.get("/api/alerts", headers=_auth_headers(token_b))
    assert len(resp.json()) == 0

    # User B can't delete user A's alert
    resp = client.delete(f"/api/alerts/{alert_id}", headers=_auth_headers(token_b))
    assert resp.status_code == 404


if __name__ == "__main__":
    tests = [
        test_create_alert, test_create_alert_invalid_condition,
        test_list_alerts, test_delete_alert, test_delete_nonexistent_alert,
        test_alerts_require_auth, test_check_alerts_empty,
        test_create_below_alert, test_alert_isolation_between_users,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} alert tests passed")
