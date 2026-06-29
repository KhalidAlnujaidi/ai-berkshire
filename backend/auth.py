"""Authentication utilities: password hashing, JWT creation/verification.

Uses passlib[bcrypt] for password hashing and python-jose (HS256) for JWT tokens.
The secret key is read from the JWT_SECRET_KEY env var. In development a
fixed fallback is used, but production MUST set a strong secret.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import User

# ── Config ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION-abc123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# ── Password hashing ────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme — token passed as Bearer header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against the stored hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    `data` should contain at least {"sub": user_id}.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token. Returns the payload or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── FastAPI Dependency ──────────────────────────────────────────────────────
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that returns the authenticated user.

    Raises 401 if the token is missing/invalid or user not found.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exc

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exc

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exc

    return user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None instead of raising 401.

    Used by endpoints that work for both authenticated and anonymous users.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    return db.query(User).filter(User.id == int(user_id)).first()
