"""Global board game catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models import BoardGame, User
from app.schemas.board_games import BoardGameCreate, BoardGameRead

router = APIRouter(prefix="/board-games", tags=["board-games"])


@router.get("", response_model=list[BoardGameRead])
def list_board_games(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BoardGame]:
    """List global catalog games with optional name search."""
    statement = select(BoardGame)
    if q:
        statement = statement.where(BoardGame.name.ilike(f"%{q}%"))
    statement = statement.order_by(BoardGame.name.asc()).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


@router.post("", response_model=BoardGameRead, status_code=status.HTTP_201_CREATED)
def create_board_game(
    payload: BoardGameCreate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardGame:
    """Create a global catalog board game."""
    board_game = BoardGame(
        name=payload.name.strip(),
        source=payload.source,
        source_id=payload.source_id,
    )
    db.add(board_game)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Board game name already exists",
        ) from exc
    db.refresh(board_game)
    return board_game
