"""Screening result repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.screening import ScreeningEvidence, ScreeningResult


class ScreeningRepository:
    @staticmethod
    def list_for_job(db: Session, job_id: int) -> list[ScreeningResult]:
        return list(db.scalars(
            select(ScreeningResult)
            .options(selectinload(ScreeningResult.evidence))
            .where(ScreeningResult.job_id == job_id)
            .order_by(ScreeningResult.rank.asc().nullslast(), ScreeningResult.final_score.desc())
        ).all())

    @staticmethod
    def get_for_candidate(db: Session, job_id: int, candidate_id: int) -> ScreeningResult | None:
        return db.scalar(
            select(ScreeningResult)
            .options(selectinload(ScreeningResult.evidence))
            .where(ScreeningResult.job_id == job_id, ScreeningResult.candidate_id == candidate_id)
        )

    @staticmethod
    def latest_for_candidate(db: Session, candidate_id: int) -> ScreeningResult | None:
        return db.scalar(
            select(ScreeningResult)
            .options(selectinload(ScreeningResult.evidence))
            .where(ScreeningResult.candidate_id == candidate_id)
            .order_by(ScreeningResult.created_at.desc())
            .limit(1)
        )

    @staticmethod
    def get(db: Session, result_id: int) -> ScreeningResult | None:
        return db.get(ScreeningResult, result_id)
