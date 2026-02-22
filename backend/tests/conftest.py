"""Pytest fixtures for backend API integration tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/board_game_tracker_test",
)
os.environ.setdefault("CORS_ORIGINS", "*")

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Return test database URL from environment."""
    return os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def db_engine(test_db_url: str):
    """Create SQLAlchemy engine for tests."""
    engine = create_engine(test_db_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def run_migrations(test_db_url: str) -> None:
    """Apply Alembic migrations to the test database once per session."""
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", test_db_url)
    command.upgrade(config, "head")


@pytest.fixture()
def clean_db(db_engine) -> Generator[None, None, None]:
    """Truncate application tables so test order does not matter."""
    table_list = "sessions,user_games,board_games,users"
    with db_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))
    yield
    with db_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db_session_factory(db_engine):
    """Return a session factory bound to the test database engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture()
def client(clean_db, db_session_factory) -> Generator[TestClient, None, None]:
    """Create a TestClient and override get_db to use the test database."""

    def override_get_db() -> Generator[Session, None, None]:
        session = db_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register and login a user, returning bearer auth headers."""
    register_payload = {
        "username": "testuser01",
        "email": "testuser01@example.com",
        "password": "Password11",
    }
    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"identifier": register_payload["username"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
