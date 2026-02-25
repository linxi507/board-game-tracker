"""Seed helpers for bootstrapping board game catalog data."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal
from app.models import BoardGame
from app.services.board_games import normalize_board_game_name


def _load_top100_names() -> list[str]:
    path = Path(__file__).resolve().parents[1] / "seed" / "top100_board_games.json"
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("top100_board_games.json must be an array of game names.")
    return [str(name).strip() for name in payload if str(name).strip()]


def seed_top100_board_games() -> tuple[int, int]:
    """Idempotently upsert Top100 entries into board_games."""
    names = _load_top100_names()
    db = SessionLocal()
    inserted = 0
    try:
        for name in names:
            normalized = normalize_board_game_name(name)
            stmt = insert(BoardGame).values(
                name=name,
                normalized_name=normalized,
                source="seed",
                source_id=None,
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=["normalized_name"])
            result = db.execute(stmt)
            inserted += result.rowcount or 0
        db.commit()
    finally:
        db.close()
    return inserted, len(names)


def seed_board_games_if_empty() -> tuple[int, int]:
    """Seed top100 only when board_games table is empty."""
    db = SessionLocal()
    try:
        existing = db.scalar(select(BoardGame.id).limit(1))
    except SQLAlchemyError:
        db.rollback()
        return 0, 0
    finally:
        db.close()

    if existing is not None:
        return 0, 0
    return seed_top100_board_games()
