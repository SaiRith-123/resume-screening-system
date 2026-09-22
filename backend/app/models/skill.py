"""Skill taxonomy and candidate-skill linkage models (spec §7, §19)."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    """Canonical skill taxonomy entry."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="other", nullable=False)
    aliases: Mapped[str] = mapped_column(String(1024), default="", nullable=False)  # comma-separated

    __table_args__ = (UniqueConstraint("canonical_name", name="uq_skills_canonical"),)


class CandidateSkill(Base, TimestampMixin):
    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[int | None] = mapped_column(
        ForeignKey("skills.id", ondelete="SET NULL"), index=True
    )
    raw_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="other", nullable=False)
    # Contextual evidence strength (spec §8D): list|summary|experience|project|certification
    evidence_context: Mapped[str] = mapped_column(String(32), default="list", nullable=False)
    evidence_strength: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    candidate: Mapped["Candidate"] = relationship(back_populates="candidate_skills")  # noqa: F821
    skill: Mapped["Skill | None"] = relationship()

    __table_args__ = (
        Index("ix_candskills_candidate_norm", "candidate_id", "normalized_name"),
        UniqueConstraint("candidate_id", "normalized_name", name="uq_candskill_cand_norm"),
    )
