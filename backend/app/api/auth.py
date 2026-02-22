"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas.auth import LoginRequest, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Register a new user account."""
    existing_username = db.scalar(select(User).where(User.username == payload.username))
    if existing_username is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_email = db.scalar(select(User).where(User.email == payload.email))
    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        message = str(exc.orig).lower() if exc.orig else ""
        if "username" in message:
            detail = "Username already exists"
        elif "email" in message:
            detail = "Email already registered"
        else:
            detail = "Failed to register user"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc

    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """Authenticate and return a bearer access token."""
    identifier = payload.identifier.strip()
    if "@" in identifier:
        user = db.scalar(select(User).where(User.email == identifier))
    else:
        user = db.scalar(select(User).where(User.username == identifier))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the current authenticated user."""
    return current_user
