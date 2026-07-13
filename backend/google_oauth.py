"""Google OAuth integration for Mizan.

Uses the authorization code flow (server-side).  Requires these env vars:

  GOOGLE_CLIENT_ID      — OAuth 2.0 client ID (Google Cloud Console)
  GOOGLE_CLIENT_SECRET  — OAuth 2.0 client secret
  GOOGLE_REDIRECT_URI   — Callback URL, e.g. https://mizan-invest.com/api/auth/google/callback

When env vars are not set, ``enabled`` is False and the endpoints return 501.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import urllib.request
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    os.getenv("CORS_ORIGINS", "http://localhost:3000"),
)

enabled: bool = bool(CLIENT_ID and CLIENT_SECRET and REDIRECT_URI)

# ── Google OAuth endpoints ────────────────────────────────────────────────

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "openid",
    "email",
    "profile",
]

# ── Helpers ────────────────────────────────────────────────────────────────


def get_authorization_url(state: str | None = None) -> str:
    """Build the Google OAuth authorization URL."""
    if state is None:
        state = secrets.token_urlsafe(32)
    params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    })
    return f"{GOOGLE_AUTH_URL}?{params}"


def exchange_code(code: str) -> dict[str, Any] | None:
    """Exchange an authorization code for tokens."""
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.error(f"Google token exchange failed: {e}")
        return None


def get_user_info(access_token: str) -> dict[str, Any] | None:
    """Fetch user profile from Google using the access token."""
    req = urllib.request.Request(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.error(f"Google userinfo failed: {e}")
        return None


def verify_id_token(id_token: str) -> dict[str, Any] | None:
    """Verify a Google ID token using Google's tokeninfo endpoint.

    This is used for the client-side (Sign In With Google) flow where
    the frontend sends the ID token directly.
    """
    params = urllib.parse.urlencode({"id_token": id_token})
    url = f"https://oauth2.googleapis.com/tokeninfo?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            # Verify the audience matches our client ID
            if data.get("aud") != CLIENT_ID:
                logger.warning(f"Google ID token audience mismatch: {data.get('aud')}")
                return None
            return data
    except Exception as e:
        logger.error(f"Google ID token verification failed: {e}")
        return None
