"""Main FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.board_games import router as board_games_router
from app.api.me import router as me_router
from app.api.sessions import router as sessions_router
from app.api.stats import router as stats_router
from app.api.user_games import router as user_games_router
from app.core.config import get_settings
from app.core.security import get_jwt_settings
from app.db import check_connection
from app.services.seed import seed_board_games_if_empty

settings = get_settings()
app = FastAPI(title="Board Game Session Tracker", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(board_games_router)
app.include_router(me_router)
app.include_router(user_games_router)
app.include_router(sessions_router)
app.include_router(stats_router)


@app.on_event("startup")
def validate_security_config() -> None:
    """Validate required security configuration at startup."""
    get_jwt_settings()
    if settings.seed_on_startup:
        seed_board_games_if_empty()


@app.get("/health")
def health():
    """Basic liveness check."""
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    """Simple liveness endpoint for deployment health checks."""
    return {"status": "ok"}


@app.get("/health-db")
def health_db():
    """Database connectivity check."""
    connected = check_connection()
    return {
        "status": "ok" if connected else "error",
        "database": "connected" if connected else "unreachable",
    }
