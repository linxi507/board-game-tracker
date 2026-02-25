"""Pydantic schema modules."""

from app.schemas.board_games import BoardGameCreate, BoardGameRead, BoardGameSummary
from app.schemas.me import (
    FavoriteRead,
    FavoriteToggleResult,
    UserCustomGameCreate,
    UserCustomGameRead,
)
from app.schemas.sessions import SessionCreate, SessionRead
from app.schemas.stats import MostPlayedGame, StatsSummary
from app.schemas.user_games import UserGameCreate, UserGameRead

__all__ = [
    "BoardGameCreate",
    "BoardGameRead",
    "BoardGameSummary",
    "FavoriteRead",
    "FavoriteToggleResult",
    "MostPlayedGame",
    "SessionCreate",
    "SessionRead",
    "StatsSummary",
    "UserCustomGameCreate",
    "UserCustomGameRead",
    "UserGameCreate",
    "UserGameRead",
]
