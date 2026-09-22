"""Screening results, evidence, and embedding models (spec §10, §13, §19, §26)."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, TimestampMixin
from app.db.types import JSONType, VectorType


class Embedding(Base, TimestampMixin):
    """Stores vector embeddings for semantic search (spec §8C, §27)."""

    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    # candidate | job | resume | evidence
    owner_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    field: Mapped[str] = mapped_column(String(64), default="text", nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    dim: Mapped[int] = mapped_column(Integer, default=settings.EMBEDDING_DIM, nullable=False)
    vector: Mapped[list] = mapped_column(VectorType, nullable=False)

    __table_args__ = (Index("ix_embeddings_owner", "owner_type", "owner_id", "field"),)


class ScreeningResult(Base, TimestampMixin):
    __tablename__ = "screening_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Component scores 0..100 (never store only the final score - spec §10)
    skill_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    project_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    certification_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    preferred_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, default=0.0, index=True, nullable=False)

    weights: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, index=True)
    eligibility_status: Mapped[str] = mapped_column(
        String(64), default="UNKNOWN", index=True, nullable=False
    )
    missing_requirements: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    matched_skills: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    partial_skills: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    missing_skills: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(64), default="review", nullable=False)
    needs_review: Mapped[bool] = mapped_column(default=True, nullable=False)
    # Serialized GenAI output (spec §32) - may be null if AI unavailable (graceful degrade)
    llm_explanation: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="screening_results")  # noqa: F821
    evidence: Mapped[list["ScreeningEvidence"]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_screening_job_final", "job_id", "final_score"),
        Index("ix_screening_job_rank", "job_id", "rank"),
    )


class ScreeningEvidence(Base, TimestampMixin):
    __tablename__ = "screening_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("screening_results.id", ondelete="CASCADE"), index=True, nullable=False
    )
    requirement: Mapped[str] = mapped_column(String(512), nullable=False)
    requirement_kind: Mapped[str] = mapped_column(String(32), default="skill", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="UNKNOWN", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_text: Mapped[str | None] = mapped_column(Text)  # must be a real resume substring
    source: Mapped[str] = mapped_column(String(32), default="resume", nullable=False)

    result: Mapped["ScreeningResult"] = relationship(back_populates="evidence")
