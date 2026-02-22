"""API-layer reusable dependencies."""

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
    """Resolve current user from a Bearer JWT."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    settings = get_jwt_settings()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings["secret_key"],
            algorithms=[settings["algorithm"]],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise unauthorized
    except JWTError as exc:
        raise unauthorized from exc

    user = db.scalar(select(User).where(User.id == int(user_id)))
    if user is None:
        raise unauthorized

    return user
