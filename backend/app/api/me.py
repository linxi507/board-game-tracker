"""Authenticated user collection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db import get_db
from app.models import BoardGame, User, UserCustomGame, UserFavoriteGame
from app.schemas.me import (
    FavoriteCreate,
    FavoriteRead,
    FavoriteToggleResult,
    UserCustomGameCreate,
    UserCustomGameRead,
)
from app.services.board_games import normalize_board_game_name

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/favorites", response_model=list[FavoriteRead])
def list_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserFavoriteGame]:
    """List favorites for the authenticated user."""
    statement = (
        select(UserFavoriteGame)
        .options(joinedload(UserFavoriteGame.board_game))
        .where(UserFavoriteGame.user_id == current_user.id)
        .order_by(UserFavoriteGame.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.post("/favorites/{board_game_id}", response_model=FavoriteToggleResult)
def toggle_favorite(
    board_game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteToggleResult:
    """Toggle favorite state for a board game."""
    board_game = db.get(BoardGame, board_game_id)
    if board_game is None:
        raise HTTPException(status_code=404, detail="Board game not found")

    favorite = db.scalar(
        select(UserFavoriteGame).where(
            UserFavoriteGame.user_id == current_user.id,
            UserFavoriteGame.board_game_id == board_game_id,
        )
    )
    if favorite is not None:
        db.delete(favorite)
        db.commit()
        return FavoriteToggleResult(board_game_id=board_game_id, is_favorite=False)

    db.add(UserFavoriteGame(user_id=current_user.id, board_game_id=board_game_id))
    db.commit()
    return FavoriteToggleResult(board_game_id=board_game_id, is_favorite=True)


@router.post("/favorites", response_model=FavoriteToggleResult)
def add_favorite(
    payload: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteToggleResult:
    """Add a board game to favorites."""
    board_game = db.get(BoardGame, payload.board_game_id)
    if board_game is None:
        raise HTTPException(status_code=404, detail="Board game not found")

    favorite = db.scalar(
        select(UserFavoriteGame).where(
            UserFavoriteGame.user_id == current_user.id,
            UserFavoriteGame.board_game_id == payload.board_game_id,
        )
    )
    if favorite is not None:
        return FavoriteToggleResult(board_game_id=payload.board_game_id, is_favorite=True)

    db.add(UserFavoriteGame(user_id=current_user.id, board_game_id=payload.board_game_id))
    db.commit()
    return FavoriteToggleResult(board_game_id=payload.board_game_id, is_favorite=True)


@router.delete("/favorites/{board_game_id}", response_model=FavoriteToggleResult)
def remove_favorite(
    board_game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteToggleResult:
    """Remove a board game from favorites."""
    favorite = db.scalar(
        select(UserFavoriteGame).where(
            UserFavoriteGame.user_id == current_user.id,
            UserFavoriteGame.board_game_id == board_game_id,
        )
    )
    if favorite is None:
        return FavoriteToggleResult(board_game_id=board_game_id, is_favorite=False)

    db.delete(favorite)
    db.commit()
    return FavoriteToggleResult(board_game_id=board_game_id, is_favorite=False)


@router.get("/custom-games", response_model=list[UserCustomGameRead])
def list_custom_games(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserCustomGame]:
    """List custom games for the authenticated user."""
    statement = (
        select(UserCustomGame)
        .where(UserCustomGame.user_id == current_user.id)
        .order_by(UserCustomGame.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.post(
    "/custom-games",
    response_model=UserCustomGameRead,
    status_code=status.HTTP_201_CREATED,
)
def create_custom_game(
    payload: UserCustomGameCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserCustomGame:
    """Create a per-user custom game."""
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name cannot be empty")

    custom_game = UserCustomGame(
        user_id=current_user.id,
        name=name,
        normalized_name=normalize_board_game_name(name),
    )
    db.add(custom_game)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom game already exists",
        ) from exc

    db.refresh(custom_game)
    return custom_game
