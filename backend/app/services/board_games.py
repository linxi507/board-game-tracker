"""Board game catalog helpers."""

from __future__ import annotations


def normalize_board_game_name(name: str) -> str:
    """Normalize a board game name for uniqueness checks and lookups."""
    return " ".join(name.strip().lower().split())
