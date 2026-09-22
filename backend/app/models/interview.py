"""Interview question model (spec §14, §19)."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class InterviewQuestion(Base, TimestampMixin):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # technical | project | behavioral | role
    kind: Mapped[str] = mapped_column(String(32), default="technical", nullable=False)
    question: Mapped[str] = mapped_column(String(1024), nullable=False)
    rationale: Mapped[str | None] = mapped_column(String(1024))
    source: Mapped[str] = mapped_column(String(32), default="llm", nullable=False)

    candidate: Mapped["Candidate"] = relationship(back_populates="interview_questions")  # noqa: F821

    __table_args__ = (Index("ix_interview_cand_job", "candidate_id", "job_id"),)
