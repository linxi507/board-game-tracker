"""Authentication API endpoints."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.google_auth import (
    build_google_authorization_url,
    exchange_code_for_identity,
    generate_google_state,
    get_google_oauth_settings,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas.auth import LoginRequest, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _google_error_redirect(detail: str) -> RedirectResponse:
    """Redirect OAuth failures back to the frontend callback page."""
    try:
        frontend_url = get_google_oauth_settings().frontend_url
    except RuntimeError:
        frontend_url = "http://localhost:5173"
    return RedirectResponse(
        url=f"{frontend_url}/auth/callback?error={quote(detail)}",
        status_code=status.HTTP_302_FOUND,
    )


def _generate_unique_username(email: str, db: Session) -> str:
    """Generate a unique username for Google-created accounts."""
    base = "".join(ch for ch in email.split("@", 1)[0].lower() if ch.isalnum()) or "user"
    base = base[:20]
    candidate = base if len(base) >= 3 else f"{base}user"[:20]
    suffix = 1
    while db.scalar(select(User.id).where(User.username == candidate)) is not None:
        suffix_text = str(suffix)
        candidate = f"{base[: max(20 - len(suffix_text), 3)]}{suffix_text}"
        suffix += 1
    return candidate


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


@router.get("/google/login")
def google_login() -> RedirectResponse:
    """Redirect the browser to Google's OAuth consent screen."""
    try:
        state = generate_google_state()
        authorization_url = build_google_authorization_url(state)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    response = RedirectResponse(url=authorization_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="google_oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=get_settings().app_env.lower() == "production",
        samesite="lax",
        path="/auth/google/callback",
    )
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Handle Google OAuth callback, map the user, and issue the app JWT."""
    if error:
        response = _google_error_redirect("Google sign-in was cancelled or failed")
        response.delete_cookie("google_oauth_state", path="/auth/google/callback")
        return response
    cookie_state = request.cookies.get("google_oauth_state")
    if not code or not state or not cookie_state or state != cookie_state:
        response = _google_error_redirect("Google sign-in failed")
        response.delete_cookie("google_oauth_state", path="/auth/google/callback")
        return response

    try:
        identity = exchange_code_for_identity(code)
    except HTTPException as exc:
        response = _google_error_redirect(exc.detail)
        response.delete_cookie("google_oauth_state", path="/auth/google/callback")
        return response

    if not identity.email_verified:
        response = _google_error_redirect("Google email is not verified")
        response.delete_cookie("google_oauth_state", path="/auth/google/callback")
        return response

    user = db.scalar(select(User).where(User.google_sub == identity.sub))
    if user is None:
        user = db.scalar(select(User).where(User.email == identity.email))
        if user is not None:
            user.google_sub = identity.sub
            user.auth_provider = "google"
        else:
            user = User(
                username=_generate_unique_username(identity.email, db),
                email=identity.email,
                password_hash=None,
                auth_provider="google",
                google_sub=identity.sub,
            )
            db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            response = _google_error_redirect("Unable to complete Google sign-in")
            response.delete_cookie("google_oauth_state", path="/auth/google/callback")
            return response
        db.refresh(user)

    access_token = create_access_token(subject=user.id)
    frontend_url = get_google_oauth_settings().frontend_url
    response = RedirectResponse(
        url=f"{frontend_url}/auth/callback?token={quote(access_token)}",
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie("google_oauth_state", path="/auth/google/callback")
    return response


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the current authenticated user."""
    return current_user
