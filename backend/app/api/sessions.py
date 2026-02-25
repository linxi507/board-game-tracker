"""Play session endpoints for authenticated users."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db import get_db
from app.models import BoardGame, Session as PlaySession, User, UserCustomGame
from app.schemas.sessions import SessionCreate, SessionRead

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaySession:
    """Create a new play session for the authenticated user."""
    if payload.board_game_id is not None:
        board_game = db.get(BoardGame, payload.board_game_id)
        if board_game is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board game not found",
            )
    else:
        custom_game = db.scalar(
            select(UserCustomGame).where(
                UserCustomGame.id == payload.user_custom_game_id,
                UserCustomGame.user_id == current_user.id,
            )
        )
        if custom_game is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom game not found",
            )

    try:
        parsed_date = datetime.strptime(payload.played_date, "%m/%d/%Y")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="played_date must be MM/DD/YYYY",
        ) from exc

    session_data = {
        "user_id": current_user.id,
        "board_game_id": payload.board_game_id,
        "user_custom_game_id": payload.user_custom_game_id,
        "played_at": parsed_date.replace(tzinfo=UTC),
        "player_count": payload.player_count,
        "placement": payload.placement,
        "duration_minutes": payload.duration_minutes,
        "notes": payload.notes,
    }

    play_session = PlaySession(**session_data)
    db.add(play_session)
    db.commit()

    created = db.scalar(
        select(PlaySession)
        .options(joinedload(PlaySession.board_game), joinedload(PlaySession.user_custom_game))
        .where(PlaySession.id == play_session.id, PlaySession.user_id == current_user.id)
    )
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created session",
        )
    return created


@router.get("", response_model=list[SessionRead])
def list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    board_game_id: int | None = Query(default=None, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlaySession]:
    """List play sessions for the authenticated user."""
    statement = (
        select(PlaySession)
        .options(joinedload(PlaySession.board_game), joinedload(PlaySession.user_custom_game))
        .where(PlaySession.user_id == current_user.id)
    )
    if board_game_id is not None:
        statement = statement.where(PlaySession.board_game_id == board_game_id)
    statement = (
        statement.order_by(desc(PlaySession.played_at), desc(PlaySession.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a session owned by the authenticated user."""
    play_session = db.scalar(
        select(PlaySession).where(
            PlaySession.id == session_id,
            PlaySession.user_id == current_user.id,
        )
    )
    if play_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    db.delete(play_session)
    db.commit()
