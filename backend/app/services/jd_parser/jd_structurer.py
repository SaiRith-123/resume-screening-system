"""Job-description structuring (spec §6).

Responsibilities are extracted SEPARATELY so they contribute to semantic
relevance but never become hard requirements automatically.
"""
from __future__ import annotations

import re

from app.core.logging import get_logger
from app.schemas.job import JobRequirementsSchema
from app.services.skill_matcher.normalizer import normalize_skills
from app.services.skill_matcher.taxonomy import SKILL_LIBRARY

logger = get_logger(__name__)

REQUIRED_MARKERS = ["required", "must have", "must-have", "requirements", "minimum",
                    "essential", "mandatory"]
PREFERRED_MARKERS = ["preferred", "nice to have", "nice-to-have", "plus", "bonus",
                     "desirable", "good to have"]
RESP_MARKERS = ["responsibilities", "what you will do", "duties", "role",
                "you will", "the role"]
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs|year)", re.IGNORECASE)
DEGREE_RE = re.compile(
    r"\b(bachelor|master|phd|doctorate|b\.?tech|m\.?tech|b\.?e\b|m\.?s\b|mba|bsc|msc)\b"
    r"[^\n.;]*", re.IGNORECASE
)


def _known_skills_in(text: str) -> list[str]:
    """Find taxonomy skills mentioned in free text."""
    found: list[str] = []
    low = text.lower()
    for canon, (_cat, aliases) in SKILL_LIBRARY.items():
        needles = [canon.lower()] + [a.lower() for a in aliases]
        for n in needles:
            if re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", low):
                found.append(canon)
                break
    return found


def _lines(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        s = raw.strip(" -•*·\t")
        if s:
            out.append(s)
    return out


def deterministic_jd(text: str) -> JobRequirementsSchema:
    lines = _lines(text)
    title = lines[0][:120] if lines else None
    required: list[str] = []
    preferred: list[str] = []
    responsibilities: list[str] = []
    mode = "general"
    for line in lines:
        low = line.lower()
        if any(m in low for m in RESP_MARKERS):
            mode = "resp"
            continue
        if any(m in low for m in PREFERRED_MARKERS):
            mode = "preferred"
            continue
        if any(m in low for m in REQUIRED_MARKERS):
            mode = "required"
            continue
        skills = _known_skills_in(line)
        if mode == "preferred" and skills:
            preferred.extend(skills)
        elif mode == "resp":
            responsibilities.append(line)
        elif skills:
            required.extend(skills)

    # fallback: if no explicit required markers, treat all found as required
    if not required:
        required = _known_skills_in(text)

    years = YEARS_RE.search(text)
    education = [m.group(0).strip() for m in DEGREE_RE.finditer(text)]

    return JobRequirementsSchema(
        job_title=title,
        required_skills=normalize_skills(required),
        preferred_skills=[s for s in normalize_skills(preferred) if s not in required],
        minimum_experience_years=float(years.group(1)) if years else None,
        education=education[:3],
        responsibilities=responsibilities[:20],
    )


def structure_job_description(text: str, llm=None) -> dict:
    base = deterministic_jd(text)
    if llm is not None:
        try:
            import asyncio
            import json

            from app.services.llm_service.prompts import jd_extraction_prompt
            from app.services.resume_parser.resume_structurer import _strip_json

            raw = asyncio.run(llm.generate(jd_extraction_prompt(text)))
            parsed = json.loads(_strip_json(raw))
            llm_schema = JobRequirementsSchema.model_validate(parsed)
            base = _merge_jd(base, llm_schema)
        except Exception as exc:  # pragma: no cover
            logger.warning("JD LLM enrichment skipped: %s", exc)
    return base.model_dump()


def _merge_jd(base: JobRequirementsSchema, extra: JobRequirementsSchema) -> JobRequirementsSchema:
    merged = base.model_copy(deep=True)
    merged.job_title = merged.job_title or extra.job_title
    for attr in ("required_skills", "preferred_skills", "required_technologies",
                 "preferred_technologies", "required_certifications",
                 "preferred_certifications", "education", "responsibilities"):
        combined = list(getattr(merged, attr))
        for item in getattr(extra, attr):
            if item not in combined:
                combined.append(item)
        setattr(merged, attr, combined)
    if merged.minimum_experience_years is None:
        merged.minimum_experience_years = extra.minimum_experience_years
    return merged


def resolve_requirements(text: str, llm=None) -> JobRequirementsSchema:
    return JobRequirementsSchema.model_validate(structure_job_description(text, llm))
