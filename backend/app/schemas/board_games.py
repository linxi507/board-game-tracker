"""Schemas for global board game catalog endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class BoardGameCreate(BaseModel):
    """Payload for creating a global catalog board game."""

    name: str = Field(min_length=1, max_length=120)
    source: str | None = Field(default=None, max_length=50)
    source_id: str | None = Field(default=None, max_length=100)


class BoardGameRead(BaseModel):
    """Global catalog board game response."""

    id: int
    name: str
    source: str | None
    source_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BoardGameSummary(BaseModel):
    """Compact board game representation for nested responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}
