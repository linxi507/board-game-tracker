"""Global board game catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models import BoardGame, User, UserCustomGame, UserFavoriteGame
from app.schemas.board_games import BoardGameCreate, BoardGameRead, BoardGameSearchItem
from app.services.board_games import normalize_board_game_name

router = APIRouter(prefix="/board-games", tags=["board-games"])


@router.get("", response_model=list[BoardGameRead])
def list_board_games(
    query: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BoardGame]:
    """List global catalog games with optional name search."""
    search_term = query if query is not None else q
    statement = select(BoardGame)
    if search_term:
        statement = statement.where(BoardGame.name.ilike(f"%{search_term}%"))
    statement = statement.order_by(BoardGame.name.asc()).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


@router.get("/search", response_model=list[BoardGameSearchItem])
def search_board_games(
    query: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BoardGameSearchItem]:
    """Unified search across custom and global board games for selector UX."""
    search_term = query.strip()
    like_pattern = f"%{search_term}%"

    custom_statement = (
        select(UserCustomGame)
        .where(UserCustomGame.user_id == current_user.id)
        .order_by(UserCustomGame.name.asc())
    )
    if search_term:
        custom_statement = custom_statement.where(UserCustomGame.name.ilike(like_pattern))
    custom_games = list(db.scalars(custom_statement.limit(limit)).all())

    is_favorite_expr = case((UserFavoriteGame.id.is_not(None), True), else_=False)
    global_statement = (
        select(BoardGame, is_favorite_expr.label("is_favorite"))
        .outerjoin(
            UserFavoriteGame,
            (UserFavoriteGame.board_game_id == BoardGame.id)
            & (UserFavoriteGame.user_id == current_user.id),
        )
        .order_by(is_favorite_expr.desc(), BoardGame.name.asc())
    )
    if search_term:
        global_statement = global_statement.where(
            BoardGame.name.ilike(like_pattern) | BoardGame.normalized_name.ilike(like_pattern)
        )
    global_rows = db.execute(global_statement.limit(limit)).all()

    items: list[BoardGameSearchItem] = []
    for game in custom_games:
        items.append(
            BoardGameSearchItem(
                key=f"custom:{game.id}",
                id=game.id,
                name=game.name,
                source="custom",
                is_favorite=False,
            )
        )
    for board_game, is_favorite in global_rows:
        items.append(
            BoardGameSearchItem(
                key=f"global:{board_game.id}",
                id=board_game.id,
                name=board_game.name,
                source="global",
                is_favorite=bool(is_favorite),
            )
        )
    return items[:limit]


@router.get("/{board_game_id}", response_model=BoardGameRead)
def get_board_game(
    board_game_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardGame:
    """Get a single board game by id."""
    board_game = db.get(BoardGame, board_game_id)
    if board_game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board game not found",
        )
    return board_game


@router.post("", response_model=BoardGameRead, status_code=status.HTTP_201_CREATED)
def create_board_game(
    payload: BoardGameCreate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardGame:
    """Create a global catalog board game."""
    name = payload.name.strip()
    board_game = BoardGame(
        name=name,
        normalized_name=normalize_board_game_name(name),
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
