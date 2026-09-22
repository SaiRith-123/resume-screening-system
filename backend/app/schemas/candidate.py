"""Candidate + screening output schemas (spec §13, §16, §17, §18, §26, §32)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.resume import ResumeSchema


class SkillMatchOut(BaseModel):
    skill: str
    status: str  # MATCH | PARTIAL_MATCH | MISSING | UNKNOWN
    confidence: float = 0.0
    strategy: str = "exact"  # exact | fuzzy | semantic | related
    context: str = "list"
    evidence: str | None = None


class ScoreBreakdown(BaseModel):
    skill_score: float
    experience_score: float
    semantic_score: float
    education_score: float
    project_score: float
    certification_score: float
    preferred_score: float
    final_score: float
    weights: dict[str, float]


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    requirement: str
    requirement_kind: str
    status: str
    confidence: float
    evidence_text: str | None = None
    source: str = "resume"


class CandidateListItem(BaseModel):
    id: int
    name: str | None
    status: str
    total_experience_years: float
    final_score: float | None = None
    rank: int | None = None
    eligibility_status: str | None = None
    skill_score: float | None = None
    experience_score: float | None = None
    semantic_score: float | None = None
    missing_requirements: list = Field(default_factory=list)
    needs_review: bool = True


class CandidateDetail(BaseModel):
    id: int
    job_id: int
    name: str | None
    email: str | None
    phone: str | None
    status: str
    processing_error: str | None
    structured: ResumeSchema
    total_experience_years: float
    created_at: datetime | None
    screening: "ScreeningResultOut | None" = None


class GenAIExplanation(BaseModel):
    summary: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    matched_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    available: bool = True
    note: str | None = None


class ScreeningResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    candidate_id: int
    job_id: int
    rank: int | None
    eligibility_status: str
    recommendation: str
    needs_review: bool
    missing_requirements: list
    matched_skills: list
    partial_skills: list
    missing_skills: list
    scores: ScoreBreakdown
    evidence: list[EvidenceOut] = Field(default_factory=list)
    explanation: GenAIExplanation | None = None

    @classmethod
    def from_orm_result(cls, r) -> "ScreeningResultOut":
        breakdown = ScoreBreakdown(
            skill_score=r.skill_score,
            experience_score=r.experience_score,
            semantic_score=r.semantic_score,
            education_score=r.education_score,
            project_score=r.project_score,
            certification_score=r.certification_score,
            preferred_score=r.preferred_score,
            final_score=r.final_score,
            weights=r.weights or {},
        )
        explanation = None
        if r.llm_explanation:
            explanation = GenAIExplanation(**r.llm_explanation)
        return cls(
            id=r.id,
            candidate_id=r.candidate_id,
            job_id=r.job_id,
            rank=r.rank,
            eligibility_status=r.eligibility_status,
            recommendation=r.recommendation,
            needs_review=r.needs_review,
            missing_requirements=r.missing_requirements or [],
            matched_skills=r.matched_skills or [],
            partial_skills=r.partial_skills or [],
            missing_skills=r.missing_skills or [],
            scores=breakdown,
            evidence=[EvidenceOut.model_validate(e) for e in r.evidence],
            explanation=explanation,
        )


class InterviewQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    question: str
    rationale: str | None = None
    source: str


class InterviewQuestionsOut(BaseModel):
    candidate_id: int
    job_id: int
    available: bool = True
    note: str | None = None
    technical: list[str] = Field(default_factory=list)
    project: list[str] = Field(default_factory=list)
    behavioral: list[str] = Field(default_factory=list)
    role: list[str] = Field(default_factory=list)
    stored: list[InterviewQuestionOut] = Field(default_factory=list)


CandidateDetail.model_rebuild()
