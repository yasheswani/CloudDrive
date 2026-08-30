from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from fastapi import Depends, HTTPException, Request

from sqlalchemy.orm import Session

from .config import settings
from .db import get_db

from app.models.models import User


# =========================================================
# PASSWORD HASHING
# =========================================================

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plain-text password using Argon2."""

    if not password:
        raise ValueError("Password cannot be empty")

    return ph.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Verify a password against an Argon2 password hash."""

    try:
        return ph.verify(
            password_hash,
            password,
        )

    except (
        VerifyMismatchError,
        VerificationError,
    ):
        return False


# =========================================================
# JWT
# =========================================================

ALG = "HS256"


def token(
    subject: str,
    days: int = 0,
    minutes: int = 0,
) -> str:
    """Create a JWT token."""

    if not subject:
        raise ValueError("Token subject cannot be empty")

    expiration = (
        datetime.now(timezone.utc)
        + timedelta(
            days=days,
            minutes=minutes,
        )
    )

    payload = {
        "sub": str(subject),
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=ALG,
    )


# =========================================================
# CURRENT USER
# =========================================================

def current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated user from the access token."""

    raw_token: Optional[str] = request.cookies.get(
        "access_token"
    )

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        payload = jwt.decode(
            raw_token,
            settings.JWT_SECRET,
            algorithms=[ALG],
        )

        subject = payload.get("sub")

        if not subject:
            raise HTTPException(
                status_code=401,
                detail="Invalid session",
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )

    try:
        user_id = int(subject)

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )

    user = db.get(
        User,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user
