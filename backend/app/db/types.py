"""Portable column types.

JSON columns use JSONB on PostgreSQL and plain JSON elsewhere, so the same
models can run on SQLite for fast unit/API tests and on PostgreSQL in production.
The embedding column maps to pgvector's ``Vector`` on PostgreSQL and stores bytes
elsewhere (the embedding table is only exercised against PostgreSQL).
"""
from __future__ import annotations

from sqlalchemy import JSON, LargeBinary
from sqlalchemy.dialects.postgresql import JSONB

from app.core.config import settings

# Pydantic-style portable JSON: JSONB on PostgreSQL, JSON otherwise.
JSONType = JSON().with_variant(JSONB, "postgresql")

try:  # pgvector is required in production; optional for SQLite-based tests
    from pgvector.sqlalchemy import Vector  # type: ignore

    VectorType = LargeBinary().with_variant(Vector(settings.EMBEDDING_DIM), "postgresql")
    HAS_PGVECTOR = True
except Exception:  # pragma: no cover
    VectorType = LargeBinary()
    HAS_PGVECTOR = False
