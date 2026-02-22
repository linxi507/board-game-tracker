"""Reusable FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_jwt_settings
from app.db import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current authenticated user from a bearer JWT."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    settings = get_jwt_settings()
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings["secret_key"],
            algorithms=[settings["algorithm"]],
        )
        subject = payload.get("sub")
        if subject is None:
            raise unauthorized
    except JWTError as exc:
        raise unauthorized from exc

    user = db.scalar(select(User).where(User.id == int(subject)))
    if user is None:
        raise unauthorized

    return user
