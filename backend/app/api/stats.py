"""Statistics endpoints for authenticated dashboard summaries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models import BoardGame, Session as PlaySession, User
from app.schemas.stats import MostPlayedGame, StatsSummary

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
def get_stats_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatsSummary:
    """Return aggregate session metrics for the current user."""
    user_filter = PlaySession.user_id == current_user.id

    total_sessions = db.scalar(
        select(func.count(PlaySession.id)).where(user_filter)
    ) or 0

    total_play_time_minutes = db.scalar(
        select(func.coalesce(func.sum(PlaySession.duration_minutes), 0)).where(user_filter)
    ) or 0

    average_duration_minutes = db.scalar(
        select(func.avg(PlaySession.duration_minutes)).where(
            user_filter,
            PlaySession.duration_minutes.is_not(None),
        )
    )

    win_count = db.scalar(
        select(func.count(PlaySession.id)).where(user_filter, PlaySession.placement == 1)
    ) or 0

    win_rate = (win_count / total_sessions) if total_sessions > 0 else None

    cutoff = datetime.now(UTC) - timedelta(days=30)
    sessions_last_30_days = db.scalar(
        select(func.count(PlaySession.id)).where(user_filter, PlaySession.played_at >= cutoff)
    ) or 0

    most_played_rows = db.execute(
        select(
            PlaySession.board_game_id,
            BoardGame.name,
            func.count(PlaySession.id).label("session_count"),
        )
        .join(BoardGame, BoardGame.id == PlaySession.board_game_id)
        .where(user_filter)
        .group_by(PlaySession.board_game_id, BoardGame.name)
        .order_by(desc("session_count"), BoardGame.name.asc())
        .limit(3)
    ).all()

    most_played_games = [
        MostPlayedGame(
            board_game_id=row.board_game_id,
            name=row.name,
            session_count=row.session_count,
        )
        for row in most_played_rows
    ]

    return StatsSummary(
        total_sessions=int(total_sessions),
        total_play_time_minutes=int(total_play_time_minutes),
        average_duration_minutes=(
            float(average_duration_minutes)
            if average_duration_minutes is not None
            else None
        ),
        win_count=int(win_count),
        win_rate=win_rate,
        sessions_last_30_days=int(sessions_last_30_days),
        most_played_games=most_played_games,
    )
