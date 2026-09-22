"""FastAPI application entrypoint (spec §3, §22, §30)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.db.session import get_db

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort DB bootstrap so a fresh container works even before migrations.
    try:
        from app.db.init_db import init_db

        init_db()
    except Exception as exc:  # pragma: no cover
        logger.warning("init_db skipped: %s", exc)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Decision-support tool that screens and ranks resumes against a job "
        "description using deterministic NLP/ML scoring plus GenAI explanations. "
        "It does not make autonomous hiring decisions."
    ),
    version="1.1.1",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)

register_exception_handlers(app)

from app.api.v1.router import api_router  # noqa: E402

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}


@app.get("/health/ready", tags=["meta"])
def health_ready(db=Depends(get_db)) -> dict:
    """Readiness probe: verifies the database answers a trivial query."""
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=503, detail={"status": "unavailable", "database": "unreachable"}
        ) from exc
    return {"status": "ok", "database": database}


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "api_prefix": settings.API_PREFIX,
        "disclaimer": (
            "This system provides decision-support recommendations. Final hiring "
            "decisions should be made by qualified human reviewers."
        ),
    }
