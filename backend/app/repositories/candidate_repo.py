"""Candidate + resume repositories."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import Candidate, Resume
from app.models.screening import ScreeningResult


class CandidateRepository:
    @staticmethod
    def create(db: Session, job_id: int, name: str | None = None) -> Candidate:
        cand = Candidate(job_id=job_id, name=name, structured={})
        db.add(cand)
        db.commit()
        db.refresh(cand)
        return cand

    @staticmethod
    def get(db: Session, candidate_id: int) -> Candidate | None:
        return db.scalar(
            select(Candidate)
            .options(
                selectinload(Candidate.resumes),
                selectinload(Candidate.screening_results).selectinload(ScreeningResult.evidence),
                selectinload(Candidate.interview_questions),
            )
            .where(Candidate.id == candidate_id)
        )

    @staticmethod
    def list_for_job(db: Session, job_id: int) -> list[Candidate]:
        return list(db.scalars(
            select(Candidate)
            .options(selectinload(Candidate.resumes))
            .where(Candidate.job_id == job_id)
            .order_by(Candidate.created_at.desc())
        ).all())

    @staticmethod
    def find_duplicate(db: Session, job_id: int, sha256: str) -> Resume | None:
        return db.scalar(
            select(Resume).join(Candidate, Resume.candidate_id == Candidate.id)
            .where(Candidate.job_id == job_id, Resume.sha256 == sha256)
        )

    @staticmethod
    def add_resume(db: Session, candidate_id: int, **fields) -> Resume:
        resume = Resume(candidate_id=candidate_id, **fields)
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume


class ResumeRepository:
    @staticmethod
    def get(db: Session, resume_id: int) -> Resume | None:
        return db.get(Resume, resume_id)
