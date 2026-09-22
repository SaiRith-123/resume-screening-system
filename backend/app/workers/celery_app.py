"""Celery application with an in-process fallback (spec §21)."""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from celery import Celery

    _HAS_CELERY = True
except Exception:  # pragma: no cover
    _HAS_CELERY = False

celery_app = None
if _HAS_CELERY:
    celery_app = Celery(
        "resume_screening",
        broker=settings.CELERY_BROKER_URL or settings.REDIS_URL or "memory://",
        backend=settings.CELERY_RESULT_BACKEND or "cache+memory://",
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        broker_connection_retry_on_startup=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )


def celery_available() -> bool:
    return bool(_HAS_CELERY and settings.USE_CELERY and (settings.CELERY_BROKER_URL or settings.REDIS_URL))
