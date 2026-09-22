"""Background tasks: resume processing + job screening (spec §21, §23).

Designed so that ONE malformed resume never crashes the whole batch.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.db.session import new_session
from app.models.candidate import Candidate, Resume
from app.services.processing import ingest_resume
from app.services.screening.pipeline import run_screening
from app.workers.celery_app import celery_app, celery_available
from app.workers.states import CandidateStatus

logger = get_logger(__name__)


def process_resume(resume_id: int, use_llm: bool = False) -> dict:
    """Extract + structure a single resume. Returns a status dict (never raises)."""
    db = new_session()
    try:
        resume = db.get(Resume, resume_id)
        if resume is None:
            return {"status": "error", "detail": "resume_not_found"}
        candidate = db.get(Candidate, resume.candidate_id)
        if candidate is None:
            return {"status": "error", "detail": "candidate_not_found"}
        try:
            ingest_resume(db, candidate, resume, use_llm=use_llm)
            return {"status": candidate.status, "candidate_id": candidate.id}
        except Exception as exc:  # noqa: BLE001
            logger.exception("process_resume failed for %s", resume_id)
            candidate.status = CandidateStatus.FAILED.value
            candidate.processing_error = f"processing_error: {exc}"
            db.commit()
            return {"status": "FAILED", "candidate_id": candidate.id, "detail": str(exc)}
    finally:
        db.close()


def screen_job(job_id: int, candidate_ids: list[int] | None = None,
               weights: dict | None = None) -> dict:
    """Screen candidates for a job. Returns a summary dict (never raises)."""
    db = new_session()
    try:
        try:
            results = run_screening(db, job_id, candidate_ids, weights)
            return {
                "status": "ok",
                "job_id": job_id,
                "count": len(results),
                "results": [
                    {"candidate_id": r.candidate_id, "final_score": r.final_score, "rank": r.rank}
                    for r in results
                ],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("screen_job failed for %s", job_id)
            return {"status": "error", "job_id": job_id, "detail": str(exc)}
    finally:
        db.close()


# --- optional Celery registration (only when a broker is configured) ----------
if celery_available() and celery_app is not None:

    @celery_app.task(name="process_resume", bind=True, max_retries=3, default_retry_delay=5)
    def process_resume_task(self, resume_id: int, use_llm: bool = False):
        try:
            return process_resume(resume_id, use_llm)
        except Exception as exc:  # pragma: no cover
            raise self.retry(exc=exc)

    @celery_app.task(name="screen_job", bind=True, max_retries=2, default_retry_delay=5)
    def screen_job_task(self, job_id: int, candidate_ids=None, weights=None):
        try:
            return screen_job(job_id, candidate_ids, weights)
        except Exception as exc:  # pragma: no cover
            raise self.retry(exc=exc)


def dispatch_process_resume(resume_id: int, use_llm: bool = False):
    """Route a resume-processing job to Celery if available, else run inline."""
    if celery_available():
        return process_resume_task.delay(resume_id, use_llm)
    return process_resume(resume_id, use_llm)


def dispatch_screen_job(job_id: int, candidate_ids=None, weights=None):
    """Route a screening job to Celery if available, else run inline."""
    if celery_available():
        return screen_job_task.delay(job_id, candidate_ids, weights)
    return screen_job(job_id, candidate_ids, weights)
