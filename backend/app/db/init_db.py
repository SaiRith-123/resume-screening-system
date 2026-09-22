"""Database bootstrap: enable pgvector and create tables (dev convenience)."""
from __future__ import annotations

from sqlalchemy import text

from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import get_engine

logger = get_logger(__name__)


def init_db() -> None:
    """Enable the pgvector extension and create any missing tables.

    In production, schema is managed by Alembic; this is a safety net so a
    fresh database still boots (spec §19, §23).
    """
    try:
        engine = get_engine()
        with engine.begin() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not enable pgvector extension: %s", exc)

    import app.models  # noqa: F401  (register all tables)

    Base.metadata.create_all(bind=get_engine())
    logger.info("Database tables ensured.")
