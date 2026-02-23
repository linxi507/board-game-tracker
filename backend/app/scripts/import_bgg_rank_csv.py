"""Import board games from a BGG rank CSV URL into the global catalog.

This script is intentionally manual and never runs automatically.
Set BGG_RANKS_CSV_URL to a CSV file URL and run:
  python -m app.scripts.import_bgg_rank_csv
"""

from __future__ import annotations

import csv
import io
import os
from urllib.request import urlopen

from sqlalchemy import select

from app.db import SessionLocal
from app.models import BoardGame
from app.services.board_games import normalize_board_game_name


def _coerce_source_id(row: dict[str, str]) -> str | None:
    for key in ("bgg_id", "id", "game_id"):
        value = (row.get(key) or "").strip()
        if value:
            return value
    return None


def _coerce_name(row: dict[str, str]) -> str | None:
    for key in ("name", "game_name", "title"):
        value = (row.get(key) or "").strip()
        if value:
            return value
    return None


def main() -> None:
    """Download, parse, and upsert board games from BGG CSV."""
    csv_url = os.getenv("BGG_RANKS_CSV_URL")
    if not csv_url:
        raise RuntimeError("BGG_RANKS_CSV_URL is required.")

    with urlopen(csv_url) as response:
        content = response.read().decode("utf-8", errors="ignore")

    reader = csv.DictReader(io.StringIO(content))

    db = SessionLocal()
    created = 0
    updated = 0
    try:
        for row in reader:
            name = _coerce_name(row)
            if not name:
                continue
            normalized_name = normalize_board_game_name(name)
            source_id = _coerce_source_id(row)

            existing = db.scalar(
                select(BoardGame).where(BoardGame.normalized_name == normalized_name)
            )
            if existing is None:
                db.add(
                    BoardGame(
                        name=name,
                        normalized_name=normalized_name,
                        source="bgg",
                        source_id=source_id,
                    )
                )
                created += 1
            else:
                if existing.name != name or existing.source != "bgg" or existing.source_id != source_id:
                    existing.name = name
                    existing.source = "bgg"
                    existing.source_id = source_id
                    updated += 1

        db.commit()
    finally:
        db.close()

    print(f"BGG import finished: created={created}, updated={updated}")


if __name__ == "__main__":
    main()
