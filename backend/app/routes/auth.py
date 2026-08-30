from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    hash_password,
    verify_password,
    token,
    current_user,
)
from app.models.models import User
from app.schemas.schemas import Register, Login


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# =========================================================
# COOKIE / TOKEN HELPERS
# =========================================================

def set_tokens(response: Response, user: User):
    """
    Set authentication tokens in secure HttpOnly cookies.

    This configuration is required because the frontend
    and backend are deployed on separate Vercel domains.
    """

    response.set_cookie(
        key="access_token",
        value=token(
            str(user.id),
            minutes=30,
        ),
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=token(
            str(user.id),
            days=14,
        ),
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )


def clear_tokens(response: Response):
    """
    Remove authentication cookies.
    """

    response.delete_cookie(
        key="access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="none",
    )

    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="none",
    )


# =========================================================
# REGISTER
# =========================================================

@router.post("/register")
def register(
    data: Register,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Create a new user account.
    """

    email = data.email.strip().lower()

    # Check if email already exists
    existing_user = (
        db.query(User)
        .filter_by(email=email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=email,
        name=data.name.strip(),
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Login immediately after registration
    set_tokens(response, user)

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
def login(
    data: Login,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate an existing user.
    """

    email = data.email.strip().lower()

    user = (
        db.query(User)
        .filter_by(email=email)
        .first()
    )

    if (
        not user
        or not user.password_hash
        or not verify_password(
            data.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    set_tokens(response, user)

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }


# =========================================================
# LOGOUT
# =========================================================

@router.post("/logout")
def logout(response: Response):
    """
    Clear authentication cookies.
    """

    clear_tokens(response)

    return {
        "ok": True,
    }


# =========================================================
# CURRENT USER
# =========================================================

@router.get("/me")
def me(
    user: User = Depends(current_user),
):
    """
    Return the currently authenticated user.
    """

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }
