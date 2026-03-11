"""Security helpers for password hashing and JWT creation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import re
from typing import TypedDict

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


class JWTSettings(TypedDict):
    """Runtime JWT settings."""

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


def get_jwt_settings() -> JWTSettings:
    """Read and validate JWT settings from environment variables."""
    settings = get_settings()

    return {
        "secret_key": settings.jwt_secret_key,
        "algorithm": settings.jwt_algorithm,
        "access_token_expire_minutes": settings.jwt_access_token_expire_minutes,
    }


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    if len(password) < 8 or len(password) > 72 or not PASSWORD_PATTERN.fullmatch(password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be 8-72 characters and contain only letters and digits",
        )
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password too long",
        )
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """Verify a plaintext password against its hash."""
    if not password_hash:
        return False
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""
    settings = get_jwt_settings()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings["access_token_expire_minutes"])
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(
        payload,
        settings["secret_key"],
        algorithm=settings["algorithm"],
    )
