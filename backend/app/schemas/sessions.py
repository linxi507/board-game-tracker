"""Schemas for play session endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.board_games import BoardGameSummary


class SessionCreate(BaseModel):
    """Payload for creating a user play session."""

    board_game_id: int = Field(ge=1)
    played_date: str
    player_count: int = Field(ge=1)
    placement: int | None = Field(default=None, ge=1)
    duration_minutes: int | None = Field(default=None, ge=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_placement(self) -> "SessionCreate":
        """Ensure optional placement is not greater than player_count."""
        if self.placement is not None and self.placement > self.player_count:
            raise ValueError("placement must be less than or equal to player_count")
        return self


class SessionRead(BaseModel):
    """Play session response for a user."""

    id: int
    board_game: BoardGameSummary
    played_at: datetime
    player_count: int
    placement: int | None
    duration_minutes: int | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
