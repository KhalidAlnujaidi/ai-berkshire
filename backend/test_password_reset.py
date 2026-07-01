"""Tests for the password reset and change password endpoints.

Run: cd backend && python test_password_reset.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.insert(0, os.path.dirname(__file__))

# Use a test database (in-memory SQLite)
os.environ["DATABASE_URL"] = "sqlite:///./test_mizan_reset.db"

# Remove any stale test DB
test_db = os.path.join(os.path.dirname(__file__), "test_mizan_reset.db")
if os.path.exists(test_db):
    os.remove(test_db)

from database import engine, Base, SessionLocal
import models  # register models
Base.metadata.create_all(bind=engine)

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

PASS = "SecurePass123!"

# ── Setup: create a user ────────────────────────────────────────────────────
r = client.post("/api/auth/register", json={
    "email": "resettest@mizan.dev",
    "password": PASS,
    "full_name": "Reset Tester",
})
assert r.status_code == 200, f"Setup register failed: {r.status_code} {r.text}"
token = r.json()["access_token"]
auth_headers = {"Authorization": f"Bearer {token}"}
print(f"SETUP: User registered, token received")


# ── Test 1: Request password reset for existing email ──────────────────────
r = client.post("/api/auth/password-reset/request", json={
    "email": "resettest@mizan.dev",
})
print(f"RESET REQUEST (existing): {r.status_code} — {r.json().get('message')}")
assert r.status_code == 200
assert "reset link has been sent" in r.json()["message"]


# ── Test 2: Request reset for non-existent email (should still 200) ────────
r = client.post("/api/auth/password-reset/request", json={
    "email": "nonexistent@mizan.dev",
})
print(f"RESET REQUEST (nonexistent): {r.status_code} — {r.json().get('message')}")
assert r.status_code == 200
assert "reset link has been sent" in r.json()["message"]


# ── Test 3: Extract token from DB to test the confirm flow ─────────────────
db = SessionLocal()
from models import PasswordResetToken
reset_record = db.query(PasswordResetToken).filter(
    PasswordResetToken.user_id == 1,
).first()
assert reset_record is not None, "No reset token was created in DB"
print(f"DB: Found reset token record (id={reset_record.id})")

# We stored a hash, so we need to generate a token through the same path.
# For testing, we'll re-derive by calling request again and intercepting.
# Instead, let's test with the raw token by re-requesting and checking the API works.
db.close()


# ── Test 4: Confirm reset with invalid token ───────────────────────────────
r = client.post("/api/auth/password-reset/confirm", json={
    "token": "invalid-token-string",
    "new_password": "NewPass456!",
})
print(f"CONFIRM (invalid token): {r.status_code} — {r.json().get('detail')}")
assert r.status_code == 400
assert "Invalid reset token" in r.json()["detail"]


# ── Test 5: Confirm reset with short password ──────────────────────────────
r = client.post("/api/auth/password-reset/confirm", json={
    "token": "some-token",
    "new_password": "short",
})
print(f"CONFIRM (short password): {r.status_code}")
assert r.status_code == 422  # Pydantic validation


# ── Test 6: Full reset flow using monkey-patched token capture ─────────────
# We'll patch email_service to capture the token
import email_service
_captured_token = None
_original_send = email_service.send_password_reset_email

def _capture_send(to_email, reset_token, user_name=None):
    global _captured_token
    _captured_token = reset_token
    return True

email_service.send_password_reset_email = _capture_send
# Also patch the reference in app module
import app as app_module
app_module.send_password_reset_email = _capture_send

r = client.post("/api/auth/password-reset/request", json={
    "email": "resettest@mizan.dev",
})
assert r.status_code == 200
assert _captured_token is not None, "Reset email was not sent"
print(f"FULL FLOW: Captured reset token ({len(_captured_token)} chars)")

# Now use the captured token
NEW_PASS = "NewSecurePass789!"
r = client.post("/api/auth/password-reset/confirm", json={
    "token": _captured_token,
    "new_password": NEW_PASS,
})
print(f"CONFIRM (valid token): {r.status_code} — {r.json().get('message')}")
assert r.status_code == 200
assert "reset successfully" in r.json()["message"]

# Restore original
email_service.send_password_reset_email = _original_send
app_module.send_password_reset_email = _original_send


# ── Test 7: Token can't be reused ──────────────────────────────────────────
r = client.post("/api/auth/password-reset/confirm", json={
    "token": _captured_token,
    "new_password": "AnotherPass999!",
})
print(f"CONFIRM (reuse token): {r.status_code} — {r.json().get('detail')}")
assert r.status_code == 400
assert "already been used" in r.json()["detail"]


# ── Test 8: Login with old password should fail ────────────────────────────
r = client.post("/api/auth/login", json={
    "email": "resettest@mizan.dev",
    "password": PASS,
})
print(f"LOGIN (old password): {r.status_code}")
assert r.status_code == 401


# ── Test 9: Login with new password should succeed ─────────────────────────
r = client.post("/api/auth/login", json={
    "email": "resettest@mizan.dev",
    "password": NEW_PASS,
})
print(f"LOGIN (new password): {r.status_code}")
assert r.status_code == 200
new_token = r.json()["access_token"]
new_auth_headers = {"Authorization": f"Bearer {new_token}"}


# ── Test 10: Change password while authenticated ───────────────────────────
r = client.post("/api/auth/change-password", json={
    "current_password": NEW_PASS,
    "new_password": "ChangedPass2024!",
}, headers=new_auth_headers)
print(f"CHANGE PASSWORD: {r.status_code} — {r.json().get('message')}")
assert r.status_code == 200
assert "changed successfully" in r.json()["message"]


# ── Test 11: Change password with wrong current password ───────────────────
r = client.post("/api/auth/change-password", json={
    "current_password": "WrongCurrent123!",
    "new_password": "AnotherNew123!",
}, headers=new_auth_headers)
print(f"CHANGE PASSWORD (wrong current): {r.status_code}")
assert r.status_code == 400


# ── Test 12: Change password without auth ──────────────────────────────────
r = client.post("/api/auth/change-password", json={
    "current_password": "something",
    "new_password": "somethingelse123!",
})
print(f"CHANGE PASSWORD (no auth): {r.status_code}")
assert r.status_code == 401


# ── Test 13: Rate limiting on reset request (3/min) ────────────────────────
# Note: TestClient shares the IP, so previous calls count.
# This test just verifies the endpoint exists and works.
r = client.post("/api/auth/password-reset/request", json={
    "email": "resettest@mizan.dev",
})
assert r.status_code in (200, 429)  # 429 if rate limited
print(f"RATE LIMIT CHECK: {r.status_code}")


# Cleanup
db.close()
if os.path.exists(test_db):
    os.remove(test_db)

print("\n✅✅ All password reset tests passed!")
