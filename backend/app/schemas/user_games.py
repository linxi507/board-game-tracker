"""Schemas for user game library endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.board_games import BoardGameSummary


class UserGameCreate(BaseModel):
    """Payload for favoriting a global board game."""

    board_game_id: int = Field(ge=1)


class UserGameRead(BaseModel):
    """User favorite board game response."""

    id: int
    board_game: BoardGameSummary
    created_at: datetime

    model_config = {"from_attributes": True}
