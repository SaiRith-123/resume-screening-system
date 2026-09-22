"""Job + job-requirement schemas (spec §6, §9, §10)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import RequirementKind, RequirementPriority


class RequirementIn(BaseModel):
    kind: RequirementKind = RequirementKind.SKILL
    priority: RequirementPriority = RequirementPriority.REQUIRED
    value: str = Field(min_length=1, max_length=512)
    min_years: float | None = None
    is_hard_gate: bool = False
    weight: float = 1.0


class ScoringWeights(BaseModel):
    skill: float = 0.35
    experience: float = 0.20
    semantic: float = 0.15
    education: float = 0.10
    project: float = 0.10
    certification: float = 0.05
    preferred: float = 0.05

    @field_validator("*")
    @classmethod
    def _non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("weights must be non-negative")
        return v

    def normalized(self) -> dict[str, float]:
        raw = self.model_dump()
        total = sum(raw.values()) or 1.0
        return {k: round(v / total, 6) for k, v in raw.items()}


class JobRequirementsSchema(BaseModel):
    """Structured JD output (spec §6)."""
    job_title: str | None = None
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    employment_type: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    required_technologies: list[str] = Field(default_factory=list)
    preferred_technologies: list[str] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)
    preferred_certifications: list[str] = Field(default_factory=list)
    minimum_experience_years: float | None = None
    preferred_experience_years: float | None = None
    education: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    employment_type: str | None = None
    requirements: list[RequirementIn] = Field(default_factory=list)
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    hard_gate: bool = False
    parse_with_llm: bool = True


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    employment_type: str | None = None
    requirements: list[RequirementIn] | None = None
    weights: ScoringWeights | None = None
    hard_gate: bool | None = None
    status: str | None = None


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    priority: str
    value: str
    normalized_value: str | None = None
    min_years: float | None = None
    is_hard_gate: bool
    weight: float


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str
    weights: dict
    hard_gate: bool
    status: str
    created_at: datetime
    requirements: list[RequirementOut] = Field(default_factory=list)


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status: str
    created_at: datetime
    candidate_count: int = 0
    average_match: float = 0.0
    top_candidate: str | None = None
