"""Google OAuth/OpenID Connect helpers."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app.core.config import get_settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = ["openid", "email", "profile"]


@dataclass(frozen=True)
class GoogleOAuthSettings:
    """Google OAuth runtime settings."""

    client_id: str
    client_secret: str
    redirect_uri: str
    frontend_url: str


@dataclass(frozen=True)
class GoogleIdentity:
    """Verified identity extracted from a Google ID token."""

    sub: str
    email: str
    email_verified: bool
    name: str | None = None


def get_google_oauth_settings() -> GoogleOAuthSettings:
    """Return validated Google OAuth settings."""
    settings = get_settings()
    missing = [
        name
        for name, value in (
            ("GOOGLE_CLIENT_ID", settings.google_client_id),
            ("GOOGLE_CLIENT_SECRET", settings.google_client_secret),
            ("GOOGLE_REDIRECT_URI", settings.google_redirect_uri),
            ("FRONTEND_URL", settings.frontend_url),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Google OAuth settings: " + ", ".join(missing)
        )
    return GoogleOAuthSettings(
        client_id=settings.google_client_id or "",
        client_secret=settings.google_client_secret or "",
        redirect_uri=settings.google_redirect_uri or "",
        frontend_url=settings.frontend_url,
    )


def generate_google_state() -> str:
    """Create a CSRF state token for the OAuth redirect."""
    return secrets.token_urlsafe(32)


def build_google_authorization_url(state: str) -> str:
    """Build the Google authorization URL for the login redirect."""
    settings = get_google_oauth_settings()
    query = urlencode(
        {
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_code_for_identity(code: str) -> GoogleIdentity:
    """Exchange an OAuth code and verify the returned Google ID token."""
    settings = get_google_oauth_settings()
    try:
        token_response = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.client_id,
                "client_secret": settings.client_secret,
                "redirect_uri": settings.redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
        token_response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange Google authorization code",
        ) from exc

    payload = token_response.json()
    raw_id_token = payload.get("id_token")
    if not raw_id_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google did not return an ID token",
        )

    try:
        claims = id_token.verify_oauth2_token(
            raw_id_token,
            Request(),
            settings.client_id,
        )
    except Exception as exc:  # google-auth raises multiple verification errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify Google identity",
        ) from exc

    return GoogleIdentity(
        sub=str(claims["sub"]),
        email=str(claims["email"]).strip().lower(),
        email_verified=bool(claims.get("email_verified")),
        name=str(claims["name"]).strip() if claims.get("name") else None,
    )
