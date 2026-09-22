"""Job posting and structured job-requirement models (spec §6, §9, §19)."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import JSONType


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
    seniority: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Per-job configurable scoring weights (spec §10)
    weights: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    # Whether missing mandatory requirements are a hard eligibility gate (spec §9)
    hard_gate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)

    owner: Mapped["User"] = relationship(back_populates="jobs")  # noqa: F821
    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    candidates: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_jobs_owner_status", "owner_id", "status"),)


class JobRequirement(Base, TimestampMixin):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # skill | experience | education | certification | technology
    kind: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    # required | preferred
    priority: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(String(512))
    min_years: Mapped[float | None] = mapped_column(Float)
    is_hard_gate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    job: Mapped["Job"] = relationship(back_populates="requirements")

    __table_args__ = (Index("ix_jobreq_job_kind_priority", "job_id", "kind", "priority"),)
