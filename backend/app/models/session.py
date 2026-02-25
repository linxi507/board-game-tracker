"""Session model for authenticated user play logs."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.board_game import BoardGame
    from app.models.user_custom_game import UserCustomGame
    from app.models.user import User


class Session(Base):
    """A single tracked play session for a user and game."""

    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("player_count >= 1", name="ck_sessions_player_count_ge_1"),
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 1",
            name="ck_sessions_duration_minutes_ge_1",
        ),
        CheckConstraint(
            "placement IS NULL OR (placement >= 1 AND placement <= player_count)",
            name="ck_sessions_placement_between_1_and_player_count",
        ),
        CheckConstraint(
            "(board_game_id IS NOT NULL AND user_custom_game_id IS NULL) OR "
            "(board_game_id IS NULL AND user_custom_game_id IS NOT NULL)",
            name="ck_sessions_exactly_one_game_reference",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    board_game_id: Mapped[int | None] = mapped_column(
        ForeignKey("board_games.id"), index=True, nullable=True
    )
    user_custom_game_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_custom_games.id"), index=True, nullable=True
    )
    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    player_count: Mapped[int] = mapped_column(nullable=False)
    placement: Mapped[int | None] = mapped_column(nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="sessions")
    board_game: Mapped["BoardGame | None"] = relationship(back_populates="sessions")
    user_custom_game: Mapped["UserCustomGame | None"] = relationship(
        back_populates="sessions"
    )
