"""Schemas for dashboard statistics endpoints."""

from pydantic import BaseModel


class MostPlayedGame(BaseModel):
    """One game entry in the top played list."""

    board_game_id: int
    name: str
    session_count: int


class StatsSummary(BaseModel):
    """Aggregated per-user dashboard metrics."""

    total_sessions: int
    total_play_time_minutes: int
    average_duration_minutes: float | None
    win_count: int
    win_rate: float | None
    sessions_last_30_days: int
    most_played_games: list[MostPlayedGame]
