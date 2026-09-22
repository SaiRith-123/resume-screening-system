"""Shared pytest fixtures.

Uses an in-memory SQLite database so unit/API tests run without PostgreSQL.
Production runs on PostgreSQL + pgvector; the portable column types in
``app.db.types`` make the same models work on both.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
import app.models  # noqa: F401  (register tables)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    from app.main import app

    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    # Note: no context-manager -> lifespan (real DB bootstrap) is not triggered.
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Isolate the in-memory rate limiter between tests."""
    from app.core import ratelimit

    ratelimit.reset_buckets()
    yield
    ratelimit.reset_buckets()


@pytest.fixture()
def auth_headers(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "tester@example.com", "full_name": "Test User", "password": "password123"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
