"""Board game model for the global catalog."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.user_game import UserGame


class BoardGame(Base):
    """Shared board game catalog entry."""

    __tablename__ = "board_games"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_games: Mapped[list["UserGame"]] = relationship(back_populates="board_game")
    sessions: Mapped[list["Session"]] = relationship(back_populates="board_game")
