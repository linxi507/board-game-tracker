"""Board game model for the global catalog."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.user_favorite_game import UserFavoriteGame
    from app.models.user_game import UserGame


class BoardGame(Base):
    """Shared board game catalog entry."""

    __tablename__ = "board_games"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_board_games_normalized_name"),
        Index(
            "uq_board_games_source_source_id_not_null",
            "source",
            "source_id",
            unique=True,
            postgresql_where=text("source_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_games: Mapped[list["UserGame"]] = relationship(back_populates="board_game")
    favorites: Mapped[list["UserFavoriteGame"]] = relationship(back_populates="board_game")
    sessions: Mapped[list["Session"]] = relationship(back_populates="board_game")
