"""User library/favorites endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db import get_db
from app.models import BoardGame, User, UserGame
from app.schemas.user_games import UserGameCreate, UserGameRead

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=UserGameRead, status_code=status.HTTP_201_CREATED)
def create_user_game(
    payload: UserGameCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserGame:
    """Favorite a board game from the global catalog."""
    board_game = db.get(BoardGame, payload.board_game_id)
    if board_game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board game not found",
        )

    user_game = UserGame(user_id=current_user.id, board_game_id=payload.board_game_id)
    db.add(user_game)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Board game already favorited",
        ) from exc

    statement = (
        select(UserGame)
        .options(joinedload(UserGame.board_game))
        .where(UserGame.id == user_game.id, UserGame.user_id == current_user.id)
    )
    created = db.scalar(statement)
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created favorite",
        )
    return created


@router.get("", response_model=list[UserGameRead])
def list_user_games(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserGame]:
    """List the current user's favorite games."""
    statement = (
        select(UserGame)
        .options(joinedload(UserGame.board_game))
        .where(UserGame.user_id == current_user.id)
        .order_by(UserGame.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.delete("/{user_game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_game(
    user_game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete one of the current user's favorites."""
    user_game = db.scalar(
        select(UserGame).where(
            UserGame.id == user_game_id,
            UserGame.user_id == current_user.id,
        )
    )
    if user_game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    db.delete(user_game)
    db.commit()
