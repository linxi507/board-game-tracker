"""Per-user favorites for global board games."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.board_game import BoardGame
    from app.models.user import User


class UserFavoriteGame(Base):
    """Favorite relation between a user and a global board game."""

    __tablename__ = "user_favorite_games"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "board_game_id",
            name="uq_user_favorite_games_user_board_game",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    board_game_id: Mapped[int] = mapped_column(
        ForeignKey("board_games.id"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="favorite_games")
    board_game: Mapped["BoardGame"] = relationship(back_populates="favorites")
