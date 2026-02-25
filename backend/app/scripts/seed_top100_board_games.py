"""Seed top 100 board games into the global catalog (idempotent)."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.models import BoardGame
from app.services.board_games import normalize_board_game_name


def _load_names() -> list[str]:
    data_path = Path(__file__).resolve().parents[1] / "seed" / "top100_board_games.json"
    with data_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("top100_board_games.json must contain a JSON array of names.")
    return [str(name).strip() for name in payload if str(name).strip()]


def main() -> None:
    """Upsert top 100 board games by normalized_name."""
    names = _load_names()
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

    print(f"Top100 seed completed. Inserted: {inserted}, attempted: {len(names)}")


if __name__ == "__main__":
    main()
