"""Database engine and session factory (lazy so imports don't require a live driver)."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine: Engine | None = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, future=True)


def get_engine() -> Engine:
    """Create the engine on first use (keeps SQLite-based tests driver-free)."""
    global _engine
    if _engine is None:
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
    return _engine


def new_session() -> Session:
    """Open a new bound session (used by workers and scripts)."""
    return SessionLocal(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    db = new_session()
    try:
        yield db
    finally:
        db.close()


def __getattr__(name: str):
    # Backwards-compatible lazy ``from app.db.session import engine``.
    if name == "engine":
        return get_engine()
    raise AttributeError(name)
