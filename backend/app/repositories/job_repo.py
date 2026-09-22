"""Job repository."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import Candidate
from app.models.job import Job, JobRequirement
from app.models.screening import ScreeningResult
from app.services.skill_matcher.normalizer import normalize_skill


class JobRepository:
    @staticmethod
    def create(db: Session, owner_id: int, data: dict, requirements: list[dict] | None = None) -> Job:
        job = Job(
            owner_id=owner_id,
            title=data["title"],
            description=data["description"],
            department=data.get("department"),
            seniority=data.get("seniority"),
            location=data.get("location"),
            employment_type=data.get("employment_type"),
            weights=data.get("weights", {}),
            hard_gate=bool(data.get("hard_gate", False)),
        )
        db.add(job)
        db.flush()
        for req in requirements or []:
            JobRepository.add_requirement(db, job.id, req)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def add_requirement(db: Session, job_id: int, req: dict) -> JobRequirement:
        row = JobRequirement(
            job_id=job_id,
            kind=req.get("kind", "skill"),
            priority=req.get("priority", "required"),
            value=req["value"],
            normalized_value=normalize_skill(req["value"]),
            min_years=req.get("min_years"),
            is_hard_gate=bool(req.get("is_hard_gate", False)),
            weight=float(req.get("weight", 1.0)),
        )
        db.add(row)
        return row

    @staticmethod
    def replace_requirements(db: Session, job: Job, requirements: list[dict]) -> None:
        from sqlalchemy import delete

        db.execute(delete(JobRequirement).where(JobRequirement.job_id == job.id))
        db.flush()
        for req in requirements:
            JobRepository.add_requirement(db, job.id, req)

    @staticmethod
    def get(db: Session, job_id: int, owner_id: int | None = None) -> Job | None:
        stmt = select(Job).options(selectinload(Job.requirements)).where(Job.id == job_id)
        if owner_id is not None:
            stmt = stmt.where(Job.owner_id == owner_id)
        return db.scalar(stmt)

    @staticmethod
    def list_for_owner(db: Session, owner_id: int) -> list[Job]:
        return list(db.scalars(
            select(Job).options(selectinload(Job.requirements))
            .where(Job.owner_id == owner_id).order_by(Job.created_at.desc())
        ).all())

    @staticmethod
    def delete(db: Session, job: Job) -> None:
        db.delete(job)
        db.commit()

    @staticmethod
    def stats(db: Session, job_id: int) -> dict:
        count = db.scalar(
            select(func.count(Candidate.id)).where(Candidate.job_id == job_id)
        ) or 0
        avg = db.scalar(
            select(func.avg(ScreeningResult.final_score)).where(ScreeningResult.job_id == job_id)
        )
        top = db.scalar(
            select(Candidate.name)
            .join(ScreeningResult, ScreeningResult.candidate_id == Candidate.id)
            .where(ScreeningResult.job_id == job_id)
            .order_by(ScreeningResult.final_score.desc())
            .limit(1)
        )
        return {"candidate_count": int(count), "average_match": round(float(avg), 1) if avg else 0.0,
                "top_candidate": top}
