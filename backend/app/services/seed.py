"""Seed helpers for bootstrapping initial board game catalog data."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal
from app.models import BoardGame

DEFAULT_BOARD_GAMES = [
    "Catan",
    "Terraforming Mars",
    "Azul",
    "Wingspan",
    "Carcassonne",
    "7 Wonders",
    "Ticket to Ride",
    "Pandemic",
    "Splendor",
    "Root",
]


def seed_board_games_if_empty() -> None:
    """Insert default catalog entries when the board_games table is empty."""
    db = SessionLocal()
    try:
        existing = db.scalar(select(BoardGame.id).limit(1))
        if existing is not None:
            return

        for name in DEFAULT_BOARD_GAMES:
            db.add(BoardGame(name=name, source="seed"))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()
