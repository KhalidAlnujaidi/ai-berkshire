"""Tests for the research engine + billing API endpoints."""

import os
import sys
import json
from pathlib import Path

# Set up test environment
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-32chars!"

# Clean any existing test database
test_db = Path(__file__).parent / "test_research.db"
if test_db.exists():
    test_db.unlink()

from fastapi.testclient import TestClient
from database import engine, SessionLocal, Base
import models  # noqa: F401
Base.metadata.create_all(bind=engine)

from app import app
client = TestClient(app)


def _register_and_login(email="researcher@test.com"):
    """Register a user and return auth headers."""
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "testpassword123",
        "full_name": "Test User",
    })
    if r.status_code == 409:
        r = client.post("/api/auth/login", json={
            "email": email,
            "password": "testpassword123",
        })
    assert r.status_code == 200, f"Auth failed: {r.status_code} {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_subscribed(email="sub@test.com"):
    """Register a user and manually set them to subscribed."""
    headers = _register_and_login(email)
    # Manually set subscription_status to active
    db = SessionLocal()
    from models import User
    user = db.query(User).filter(User.email == email).first()
    user.subscription_status = "active"
    user.subscription_plan = "monthly"
    db.commit()
    db.close()
    return headers


# ── Tests ────────────────────────────────────────────────────────────────────

def test_health():
    """Basic health check still works."""
    r = client.get("/api/health")
    assert r.status_code == 200


def test_samples_public():
    """GET /api/research/samples is public (no auth)."""
    r = client.get("/api/research/samples")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # Should have at least the RKLB sample (if seeding worked)
    if data:
        assert data[0]["is_sample"] == True
        assert "report_markdown" in data[0]


def test_research_requires_auth():
    """POST /api/research without auth → 401."""
    r = client.post("/api/research", json={"ticker": "AAPL"})
    assert r.status_code == 401


def test_research_requires_subscription():
    """POST /api/research with free user → 402."""
    headers = _register_and_login("free@test.com")
    r = client.post("/api/research", json={"ticker": "AAPL"}, headers=headers)
    assert r.status_code == 402
    assert "Subscription required" in r.json()["detail"]


def test_billing_subscription_status():
    """GET /api/billing/subscription returns status."""
    headers = _register_and_login("bill@test.com")
    r = client.get("/api/billing/subscription", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "free"
    assert data["is_subscribed"] == False


def test_billing_subscription_active():
    """Subscribed user gets is_subscribed=true."""
    headers = _make_subscribed("active@test.com")
    r = client.get("/api/billing/subscription", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["is_subscribed"] == True
    assert data["plan"] == "monthly"


def test_research_history_requires_auth():
    """GET /api/research/history without auth → 401."""
    r = client.get("/api/research/history")
    assert r.status_code == 401


def test_research_history_empty():
    """GET /api/research/history for new user returns empty list."""
    headers = _make_subscribed("history@test.com")
    r = client.get("/api/research/history", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


def test_get_nonexistent_report():
    """GET /api/research/{job_id} with bad ID → 404."""
    headers = _make_subscribed("nonexist@test.com")
    r = client.get("/api/research/99999", headers=headers)
    assert r.status_code == 404


if __name__ == "__main__":
    # Run tests manually
    import traceback
    tests = [
        test_health,
        test_samples_public,
        test_research_requires_auth,
        test_research_requires_subscription,
        test_billing_subscription_status,
        test_billing_subscription_active,
        test_research_history_requires_auth,
        test_research_history_empty,
        test_get_nonexistent_report,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
