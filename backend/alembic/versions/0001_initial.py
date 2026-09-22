"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00

Creates the pgvector extension and all application tables. Table definitions
are derived from the SQLAlchemy metadata so the migration stays in lock-step
with the ORM models in ``app.models``.
"""
from __future__ import annotations

from alembic import op

from app.db.base import Base
import app.models  # noqa: F401  (register all tables)

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
