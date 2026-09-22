"""Candidate detail + GenAI endpoints (spec §18, §20)."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.screening_repo import ScreeningRepository
from app.schemas.candidate import (
    CandidateDetail,
    GenAIExplanation,
    InterviewQuestionsOut,
    ScreeningResultOut,
)
from app.schemas.resume import ResumeSchema
from app.services.llm_service.genai import (
    fallback_interview_questions,
    generate_interview_questions,
    generate_screening_explanation,
)
from app.services.llm_service.providers import get_llm_provider
from app.utils.files import read_stored_file

router = APIRouter(prefix="/candidates", tags=["candidates"])


def _job_summary(job) -> dict:
    return {
        "job_title": job.title,
        "description": job.description[:3000],
        "required": [r.value for r in job.requirements if r.priority == "required"],
        "preferred": [r.value for r in job.requirements if r.priority == "preferred"],
        "responsibilities": [],
    }


def _owned_candidate(db: Session, candidate_id: int, user: User):
    cand = CandidateRepository.get(db, candidate_id)
    if cand is None or JobRepository.get(db, cand.job_id, user.id) is None:
        raise NotFoundError("Candidate not found")
    return cand


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(candidate_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)) -> CandidateDetail:
    cand = _owned_candidate(db, candidate_id, user)
    res = ScreeningRepository.get_for_candidate(db, cand.job_id, candidate_id)
    return CandidateDetail(
        id=cand.id, job_id=cand.job_id, name=cand.name, email=cand.email, phone=cand.phone,
        status=cand.status, processing_error=cand.processing_error,
        structured=ResumeSchema.model_validate(cand.structured or {}),
        total_experience_years=cand.total_experience_years,
        created_at=cand.created_at,
        screening=ScreeningResultOut.from_orm_result(res) if res else None,
    )


@router.get("/{candidate_id}/resume")
def download_resume(candidate_id: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)) -> Response:
    cand = _owned_candidate(db, candidate_id, user)
    if not cand.resumes:
        raise NotFoundError("Resume not found")
    resume = cand.resumes[0]
    if resume.stored_path.startswith("s3://"):
        return Response(
            content=read_stored_file(resume.stored_path),
            media_type=resume.content_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{resume.original_filename}"'},
        )
    return FileResponse(resume.stored_path, filename=resume.original_filename,
                        media_type=resume.content_type or "application/octet-stream")


@router.get("/{candidate_id}/explanation")
def explain(candidate_id: int, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    cand = _owned_candidate(db, candidate_id, user)
    job = JobRepository.get(db, cand.job_id, user.id)
    res = ScreeningRepository.get_for_candidate(db, cand.job_id, candidate_id)
    if res is None:
        raise NotFoundError("No screening result for candidate")
    computed = {
        "final_score": res.final_score, "skill_score": res.skill_score,
        "experience_score": res.experience_score, "semantic_score": res.semantic_score,
        "education_score": res.education_score, "project_score": res.project_score,
        "certification_score": res.certification_score, "preferred_score": res.preferred_score,
        "eligibility_status": res.eligibility_status, "weights": res.weights,
    }
    evidence = [
        {"requirement": e.requirement, "status": e.status, "evidence": e.evidence_text}
        for e in res.evidence
    ]
    result = asyncio.run(generate_screening_explanation(
        cand.structured or {}, _job_summary(job), computed, evidence
    ))
    # persist for history (spec §22 history of screening)
    res.llm_explanation = {k: v for k, v in result.items() if k not in ("kind",)}
    db.commit()
    return result


@router.post("/{candidate_id}/interview-questions", response_model=InterviewQuestionsOut)
def interview_questions(candidate_id: int, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)) -> InterviewQuestionsOut:
    cand = _owned_candidate(db, candidate_id, user)
    job = JobRepository.get(db, cand.job_id, user.id)
    res = ScreeningRepository.get_for_candidate(db, cand.job_id, candidate_id)
    matched = (res.matched_skills if res else []) or []
    missing = (res.missing_skills if res else []) or []

    provider = get_llm_provider()
    if getattr(provider, "name", "") == "null":
        data = fallback_interview_questions(cand.structured or {}, matched, missing)
    else:
        data = asyncio.run(generate_interview_questions(
            cand.structured or {}, _job_summary(job), matched, missing, provider=provider
        ))
        if not data.get("available"):
            data = fallback_interview_questions(cand.structured or {}, matched, missing)

    # persist generated questions (history)
    from app.models.interview import InterviewQuestion

    for kind in ("technical", "project", "behavioral", "role"):
        for q in data.get(kind, []):
            db.add(InterviewQuestion(candidate_id=cand.id, job_id=cand.job_id,
                                     kind=kind, question=q[:1000],
                                     source="llm" if data.get("available") else "rule"))
    db.commit()

    return InterviewQuestionsOut(
        candidate_id=cand.id, job_id=cand.job_id,
        available=data.get("available", False), note=data.get("note"),
        technical=data.get("technical", []), project=data.get("project", []),
        behavioral=data.get("behavioral", []), role=data.get("role", []),
        stored=cand.interview_questions,
    )
