"""Candidate profile, resume, and structured sub-entity models (spec §5, §11, §19)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import JSONType
from app.workers.states import CandidateStatus


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255), index=True)
    # Identity/contact kept SEPARATE from evaluation features (spec §15)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    summary: Mapped[str | None] = mapped_column(Text)
    total_experience_years: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default=CandidateStatus.UPLOADED.value, index=True, nullable=False
    )
    processing_error: Mapped[str | None] = mapped_column(Text)
    # Full validated structured resume JSON (spec §5)
    structured: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    job: Mapped["Job"] = relationship(back_populates="candidates")  # noqa: F821
    resumes: Mapped[list["Resume"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
    candidate_skills: Mapped[list["CandidateSkill"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    education: Mapped[list["Education"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    screening_results: Mapped[list["ScreeningResult"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
    interview_questions: Mapped[list["InterviewQuestion"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_candidates_job_status", "job_id", "status"),
        Index("ix_candidates_job_name", "job_id", "name"),
    )


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(default=0, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str | None] = mapped_column(String(32))  # native|ocr|failed
    page_count: Mapped[int | None] = mapped_column()

    candidate: Mapped["Candidate"] = relationship(back_populates="resumes")

    __table_args__ = (Index("ix_resumes_candidate_sha", "candidate_id", "sha256"),)


class Experience(Base, TimestampMixin):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)
    # internship | full-time | freelance | academic
    kind: Mapped[str] = mapped_column(String(32), default="full-time", nullable=False)
    duration_months: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    candidate: Mapped["Candidate"] = relationship(back_populates="experiences")


class Education(Base, TimestampMixin):
    __tablename__ = "education"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    degree: Mapped[str | None] = mapped_column(String(255))
    field_of_study: Mapped[str | None] = mapped_column(String(255))
    institution: Mapped[str | None] = mapped_column(String(255))
    start_year: Mapped[int | None] = mapped_column()
    end_year: Mapped[int | None] = mapped_column()
    grade: Mapped[str | None] = mapped_column(String(64))

    candidate: Mapped["Candidate"] = relationship(back_populates="education")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    technologies: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)

    candidate: Mapped["Candidate"] = relationship(back_populates="projects")


class Certification(Base, TimestampMixin):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255))
    issuer: Mapped[str | None] = mapped_column(String(255))
    year: Mapped[int | None] = mapped_column()

    candidate: Mapped["Candidate"] = relationship(back_populates="certifications")
