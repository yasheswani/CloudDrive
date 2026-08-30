from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    hash_password,
    verify_password,
    token,
    current_user,
    cookie_options,
)

from app.models.models import User
from app.schemas.schemas import Register, Login


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# =========================================================
# SET AUTHENTICATION COOKIES
# =========================================================

def set_tokens(response: Response, user: User) -> None:
    """
    Create access and refresh cookies for the user.
    """

    options = cookie_options()

    access_token = token(
        str(user.id),
        minutes=30,
    )

    refresh_token = token(
        str(user.id),
        days=14,
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=30 * 60,
        **options,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=14 * 24 * 60 * 60,
        **options,
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

    user = User(
        email=email,
        name=data.name.strip(),
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

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
    Completely remove the authentication cookies.
    """

    options = cookie_options()

    response.delete_cookie(
        key="access_token",
        path=options["path"],
    )

    response.delete_cookie(
        key="refresh_token",
        path=options["path"],
    )

    return {
        "ok": True,
        "message": "Logged out successfully",
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
