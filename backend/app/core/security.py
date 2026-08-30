from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from fastapi import Depends, HTTPException, Request

from sqlalchemy.orm import Session

from .config import settings
from .db import get_db

from app.models.models import User


# ---------------------------------------------------------
# Password hashing
# ---------------------------------------------------------
# Argon2 is used instead of bcrypt/Passlib.
# This avoids the bcrypt compatibility issue you encountered.
ph = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2.
    """
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain-text password against an Argon2 hash.
    """
    try:
        return ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


# ---------------------------------------------------------
# JWT configuration
# ---------------------------------------------------------

ALG = "HS256"


def token(subject: str, days: int = 0, minutes: int = 0) -> str:
    """
    Create a JWT token for the given user ID.
    """

    exp = datetime.now(timezone.utc) + timedelta(
        days=days,
        minutes=minutes
    )

    payload = {
        "sub": str(subject),
        "exp": exp,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=ALG,
    )


# ---------------------------------------------------------
# Current authenticated user
# ---------------------------------------------------------

def current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get the currently authenticated user from the
    access_token HttpOnly cookie.
    """

    raw = request.cookies.get("access_token")

    if not raw:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        payload = jwt.decode(
            raw,
            settings.JWT_SECRET,
            algorithms=[ALG],
        )

        sub = payload.get("sub")

        if not sub:
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
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user