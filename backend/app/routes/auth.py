from fastapi import APIRouter, Depends, HTTPException, Response
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
# SET AUTHENTICATION COOKIES
# =========================================================

def set_tokens(
    response: Response,
    user: User,
):
    """
    Store JWT access and refresh tokens
    in secure HttpOnly cookies.

    secure=True and samesite="none" are required
    because frontend and backend are deployed
    separately on Vercel.
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


# =========================================================
# CLEAR AUTHENTICATION COOKIES
# =========================================================

def clear_tokens(
    response: Response,
):
    response.delete_cookie(
        key="access_token",
        path="/",
    )

    response.delete_cookie(
        key="refresh_token",
        path="/",
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
    email = data.email.strip().lower()

    # Check existing user
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
        password_hash=hash_password(
            data.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Login immediately
    set_tokens(
        response,
        user,
    )

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
    email = data.email.strip().lower()

    user = (
        db.query(User)
        .filter_by(email=email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    set_tokens(
        response,
        user,
    )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }


# =========================================================
# LOGOUT
# =========================================================

@router.post("/logout")
def logout(
    response: Response,
):
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
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }
