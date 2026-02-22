"""Pydantic schemas for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field

USERNAME_PATTERN = r"^[A-Za-z0-9]+$"
PASSWORD_PATTERN = r"^[A-Za-z0-9]+$"


class UserCreate(BaseModel):
    """Request body for user registration."""

    username: str = Field(min_length=3, max_length=20, pattern=USERNAME_PATTERN)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=72, pattern=PASSWORD_PATTERN)


class LoginRequest(BaseModel):
    """Request body for user login."""

    identifier: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=72, pattern=PASSWORD_PATTERN)


class UserRead(BaseModel):
    """User response shape."""

    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: str
