"""Resume structured-extraction schema (spec §5) - validates LLM + deterministic output."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ContactInfo(BaseModel):
    email: str | None = None
    phone: str | None = None


class EducationItem(BaseModel):
    degree: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    grade: str | None = None


class ExperienceItem(BaseModel):
    company: str | None = None
    title: str | None = None
    description: str | None = None
    start_date: str | None = None  # ISO date or partial
    end_date: str | None = None
    is_current: bool = False
    kind: str = "full-time"  # internship | full-time | freelance | academic
    duration_months: float = 0.0


class ProjectItem(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    name: str | None = None
    issuer: str | None = None
    year: int | None = None


class ResumeSchema(BaseModel):
    candidate_name: str | None = None
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_technologies: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    total_experience_years: float = 0.0
    # NOTE: sensitive attributes (gender, age/DOB, race, religion, marital status,
    # photo) are intentionally NOT modelled and must never be scored (spec §15).

    @field_validator("skills", "technical_skills", "soft_skills", "programming_languages",
                     "frameworks", "databases", "cloud_technologies", "tools", "languages",
                     mode="before")
    @classmethod
    def _coerce_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v
