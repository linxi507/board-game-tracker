"""Schemas for authenticated user favorites/custom collection APIs."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.board_games import BoardGameSummary


class FavoriteToggleResult(BaseModel):
    """Toggle result for favorites endpoint."""

    board_game_id: int
    is_favorite: bool


class FavoriteRead(BaseModel):
    """One favorite game entry for current user."""

    id: int
    board_game: BoardGameSummary
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCustomGameCreate(BaseModel):
    """Create a custom game for the current user."""

    name: str = Field(min_length=1, max_length=255)


class UserCustomGameRead(BaseModel):
    """Custom game owned by current user."""

    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
