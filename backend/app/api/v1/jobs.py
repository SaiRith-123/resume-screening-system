"""Job CRUD endpoints (spec §20)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.job_repo import JobRepository
from app.schemas.common import MessageOut
from app.schemas.job import JobCreate, JobListItem, JobOut, JobUpdate
from app.services.jd_parser.jd_structurer import resolve_requirements
from app.services.skill_matcher.normalizer import normalize_skill

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _derive_requirements(payload: JobCreate) -> list[dict]:
    """Merge explicitly provided requirements with LLM/deterministic JD parsing."""
    reqs: list[dict] = [
        {
            "kind": r.kind.value if hasattr(r.kind, "value") else r.kind,
            "priority": r.priority.value if hasattr(r.priority, "value") else r.priority,
            "value": r.value,
            "min_years": r.min_years,
            "is_hard_gate": r.is_hard_gate,
            "weight": r.weight,
        }
        for r in payload.requirements
    ]
    if not reqs:
        llm = None
        if payload.parse_with_llm:
            try:
                from app.services.llm_service.providers import get_llm_provider

                candidate_llm = get_llm_provider()
                llm = None if getattr(candidate_llm, "name", "") == "null" else candidate_llm
            except Exception:
                llm = None
        parsed = resolve_requirements(payload.description, llm)
        for s in parsed.required_skills:
            reqs.append({"kind": "skill", "priority": "required", "value": s})
        for s in parsed.preferred_skills:
            reqs.append({"kind": "skill", "priority": "preferred", "value": s})
        if parsed.minimum_experience_years:
            reqs.append({
                "kind": "experience", "priority": "required", "value": "minimum experience",
                "min_years": parsed.minimum_experience_years, "is_hard_gate": False,
            })
        for e in parsed.education:
            reqs.append({"kind": "education", "priority": "required", "value": e})
    return reqs


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)) -> JobOut:
    reqs = _derive_requirements(payload)
    weights = payload.weights.normalized()
    job = JobRepository.create(
        db, user.id,
        {
            "title": payload.title, "description": payload.description,
            "department": payload.department, "seniority": payload.seniority,
            "location": payload.location, "employment_type": payload.employment_type,
            "weights": weights, "hard_gate": payload.hard_gate,
        },
        reqs,
    )
    _ = normalize_skill  # keep import used for requirement normalization
    return JobOut.model_validate(job)


@router.get("", response_model=list[JobListItem])
def list_jobs(
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List the recruiter's jobs. Paginated via ?page=&page_size= + X-Total-Count."""
    all_jobs = JobRepository.list_for_owner(db, user.id)
    response.headers["X-Total-Count"] = str(len(all_jobs))
    window = all_jobs[(page - 1) * page_size: page * page_size]
    out: list[JobListItem] = []
    for job in window:
        stats = JobRepository.stats(db, job.id)
        out.append(JobListItem(
            id=job.id, title=job.title, status=job.status, created_at=job.created_at,
            candidate_count=stats["candidate_count"], average_match=stats["average_match"],
            top_candidate=stats["top_candidate"],
        ))
    return out

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> JobOut:
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")
    return JobOut.model_validate(job)


@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)) -> JobOut:
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")
    data = payload.model_dump(exclude_unset=True)
    reqs = data.pop("requirements", None)
    weights = data.pop("weights", None)
    if weights is not None:
        job.weights = _normalize_weights(weights)
    for key, value in data.items():
        setattr(job, key, value)
    if reqs is not None:
        JobRepository.replace_requirements(db, job, [req.model_dump() for req in reqs])
    db.commit()
    db.refresh(job)
    return JobOut.model_validate(job)


@router.delete("/{job_id}", response_model=MessageOut)
def delete_job(job_id: int, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)) -> MessageOut:
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")
    JobRepository.delete(db, job)
    return MessageOut(message="Job deleted")


def _normalize_weights(weights: dict) -> dict:
    from app.schemas.job import ScoringWeights

    return ScoringWeights(**weights).normalized()
