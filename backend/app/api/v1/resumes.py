"""Resume upload + screening endpoints (spec §20, §21, §22)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import NotFoundError, UploadError
from app.db.session import get_db
from app.models.user import User
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.screening_repo import ScreeningRepository
from app.schemas.candidate import CandidateListItem, ScreeningResultOut
from app.schemas.common import MessageOut
from app.services.processing import ingest_resume
from app.services.screening.pipeline import run_screening
from app.services.skill_matcher.normalizer import normalize_skill
from app.utils.files import FileValidationError, store_upload

router = APIRouter(prefix="/jobs/{job_id}", tags=["resumes"])


@router.post("/resumes", status_code=status.HTTP_201_CREATED)
async def upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    auto_screen: bool = True,
    use_llm: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")

    accepted, rejected = [], []
    candidate_ids: list[int] = []
    for upload in files:
        content = await upload.read()
        try:
            validated = store_upload(upload.filename, content, upload.content_type, job_id)
        except FileValidationError as exc:
            rejected.append({"filename": upload.filename, "reason": str(exc)})
            continue

        if CandidateRepository.find_duplicate(db, job_id, validated.sha256):
            rejected.append({"filename": upload.filename, "reason": "duplicate_resume"})
            continue

        candidate = CandidateRepository.create(db, job_id)
        CandidateRepository.add_resume(
            db, candidate.id,
            original_filename=validated.safe_name,
            stored_path=validated.stored_path,
            content_type=validated.content_type,
            size_bytes=validated.size_bytes,
            sha256=validated.sha256,
        )
        # process synchronously for reliability (async path available via Celery)
        try:
            ingest_resume(db, candidate, candidate.resumes[0], use_llm=use_llm)
        except Exception as exc:  # noqa: BLE001
            candidate.processing_error = f"processing_error: {exc}"
        if candidate.status == "ANALYZED":
            candidate_ids.append(candidate.id)
        accepted.append({"candidate_id": candidate.id, "filename": validated.safe_name,
                         "status": candidate.status, "processing_error": candidate.processing_error})

    screenings = []
    if auto_screen and candidate_ids:
        screenings = run_screening(db, job_id, candidate_ids)

    return {
        "accepted": accepted,
        "rejected": rejected,
        "screened": len(screenings),
    }


@router.get("/candidates", response_model=list[CandidateListItem])
def list_candidates(
    job_id: int,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CandidateListItem]:
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")
    all_candidates = CandidateRepository.list_for_job(db, job_id)
    response.headers["X-Total-Count"] = str(len(all_candidates))
    out: list[CandidateListItem] = []
    for cand in all_candidates[(page - 1) * page_size: page * page_size]:
        res = ScreeningRepository.get_for_candidate(db, job_id, cand.id)
        out.append(CandidateListItem(
            id=cand.id, name=cand.name, status=cand.status,
            total_experience_years=cand.total_experience_years,
            final_score=res.final_score if res else None,
            rank=res.rank if res else None,
            eligibility_status=res.eligibility_status if res else None,
            skill_score=res.skill_score if res else None,
            experience_score=res.experience_score if res else None,
            semantic_score=res.semantic_score if res else None,
            missing_requirements=(res.missing_requirements if res else []) or [],
            needs_review=res.needs_review if res else True,
        ))
    return out


@router.post("/screen", response_model=dict)
def screen(job_id: int, candidate_ids: list[int] | None = None,
           db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")
    results = run_screening(db, job_id, candidate_ids)
    return {"screened": len(results)}


@router.get("/results", response_model=list[ScreeningResultOut])
def results(
    job_id: int,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ScreeningResultOut]:
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")
    all_results = ScreeningRepository.list_for_job(db, job_id)
    response.headers["X-Total-Count"] = str(len(all_results))
    window = all_results[(page - 1) * page_size: page * page_size]
    return [ScreeningResultOut.from_orm_result(r) for r in window]
