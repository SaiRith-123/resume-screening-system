"""GenAI features (spec §14, §32). All are additive and degrade gracefully.

Every function returns a dict that validates against a Pydantic model and is
grounded: evidence that is not a substring of the resume is dropped.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.llm_service.guardrails import (
    filter_sensitive_questions,
    sanitize_untrusted,
)
from app.services.llm_service.prompts import (
    candidate_summary_prompt,
    interview_questions_prompt,
    screening_explanation_prompt,
)
from app.services.llm_service.provider import LLMProvider, LLMUnavailableError
from app.services.llm_service.providers import get_llm_provider
from app.services.screening.evidence import is_grounded

logger = get_logger(__name__)

AI_UNAVAILABLE_NOTE = (
    "AI explanation unavailable. Deterministic screening results are still available."
)


class SummaryOut(BaseModel):
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ExplanationOut(BaseModel):
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    matched_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class QuestionsOut(BaseModel):
    technical: list[str] = Field(default_factory=list)
    project: list[str] = Field(default_factory=list)
    behavioral: list[str] = Field(default_factory=list)
    role: list[str] = Field(default_factory=list)


def _unavailable(kind: str) -> dict:
    return {"available": False, "note": AI_UNAVAILABLE_NOTE, "kind": kind}


async def generate_candidate_summary(candidate: dict, job_summary: dict, computed: dict,
                                     provider: LLMProvider | None = None) -> dict:
    provider = provider or get_llm_provider()
    prompt = candidate_summary_prompt(sanitize_untrusted(str(candidate)), job_summary, computed)
    try:
        data = await provider.generate_json(prompt, SummaryOut)
        data["available"] = True
        return data
    except LLMUnavailableError as exc:
        logger.info("summary unavailable: %s", exc)
        return _unavailable("summary")


async def generate_screening_explanation(candidate: dict, job_summary: dict, computed: dict,
                                         evidence: list[dict],
                                         provider: LLMProvider | None = None) -> dict:
    provider = provider or get_llm_provider()
    prompt = screening_explanation_prompt(
        sanitize_untrusted(str(candidate)), job_summary, computed, evidence
    )
    resume_text = str(candidate)
    try:
        data = await provider.generate_json(prompt, ExplanationOut)
        # drop any evidence the model invented (grounding check, spec §13/§31)
        data["evidence"] = [e for e in data.get("evidence", []) if is_grounded(e, resume_text)]
        data["available"] = True
        return data
    except LLMUnavailableError as exc:
        logger.info("explanation unavailable: %s", exc)
        return _unavailable("explanation")


async def generate_interview_questions(candidate: dict, job_summary: dict,
                                       matched: list[str], missing: list[str],
                                       provider: LLMProvider | None = None) -> dict:
    provider = provider or get_llm_provider()
    prompt = interview_questions_prompt(
        sanitize_untrusted(str(candidate)), job_summary, matched, missing
    )
    try:
        data = await provider.generate_json(prompt, QuestionsOut)
        for key in ("technical", "project", "behavioral", "role"):
            data[key] = filter_sensitive_questions(data.get(key, []))
        data["available"] = True
        return data
    except LLMUnavailableError as exc:
        logger.info("interview questions unavailable: %s", exc)
        return _unavailable("interview_questions")


# ---- deterministic fallbacks so the UI is never empty (spec §23) -------------

def fallback_interview_questions(candidate: dict, matched: list[str],
                                 missing: list[str]) -> dict:
    tech = [f"Walk me through a project where you used {s} in production." for s in matched[:4]]
    tech += [f"How would you ramp up on {s}, which this role requires?" for s in missing[:3]]
    proj = [
        f"Describe the architecture of '{p.get('name')}' and your specific contribution."
        for p in (candidate.get("projects") or [])[:3]
    ]
    behav = [
        "Tell me about a time you disagreed with a teammate on a technical decision.",
        "Describe a project that failed and what you learned.",
        "How do you prioritize when deadlines are tight?",
    ]
    role = [
        "Why are you interested in this role specifically?",
        "How do you keep your technical skills current?",
    ]
    return {
        "technical": tech, "project": proj, "behavioral": behav, "role": role,
        "available": False, "note": AI_UNAVAILABLE_NOTE,
    }
