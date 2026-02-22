"""Database engine and session factory.

Reads DATABASE_URL from the environment and creates a SQLAlchemy 2.0
engine and session factory. Provides a `get_db` dependency for FastAPI
and a `check_connection` helper for health checks.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

DATABASE_URL = get_settings().database_url

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all future SQLAlchemy models."""
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    """Return True if the database is reachable (SELECT 1), False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
