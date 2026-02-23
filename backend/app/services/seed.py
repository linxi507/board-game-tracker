"""Seed helpers for bootstrapping initial board game catalog data."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal
from app.models import BoardGame
from app.services.board_games import normalize_board_game_name

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
    "Gloomhaven",
    "Scythe",
    "Brass: Birmingham",
    "Spirit Island",
    "Everdell",
    "Dune: Imperium",
    "The Castles of Burgundy",
    "Concordia",
    "Dominion",
    "Ark Nova",
]


def seed_board_games_if_empty() -> None:
    """Insert default catalog entries idempotently by normalized_name."""
    db = SessionLocal()
    try:
        normalized_defaults = {
            normalize_board_game_name(name): name for name in DEFAULT_BOARD_GAMES
        }
        existing = db.scalars(
            select(BoardGame.normalized_name).where(
                BoardGame.normalized_name.in_(list(normalized_defaults.keys()))
            )
        ).all()
        existing_set = set(existing)

        for normalized_name, display_name in normalized_defaults.items():
            if normalized_name in existing_set:
                continue
            db.add(
                BoardGame(
                    name=display_name,
                    normalized_name=normalized_name,
                    source="seed",
                )
            )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()
