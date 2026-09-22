"""Deterministic resume structuring with optional LLM enrichment (spec §5).

Output is validated by ``ResumeSchema``. The deterministic pass always runs;
the LLM pass is additive and its output is merged only where it does not
contradict deterministic findings (spec §5: "do not blindly trust LLM extraction").
"""
from __future__ import annotations

import re

from app.core.logging import get_logger
from app.schemas.resume import ResumeSchema
from app.services.resume_parser.section_detector import detect_sections
from app.services.skill_matcher.normalizer import normalize_skills
from app.services.skill_matcher.taxonomy import category_of

logger = get_logger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
YEAR_RE = re.compile(r"(?:19|20)\d{2}")
DATE_RANGE_RE = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{4})"
    r"\s*(?:-|–|to)\s*"
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{4}|present|current)",
    re.IGNORECASE,
)
DEGREE_KEYWORDS = ["b.tech", "btech", "b.e", "bachelor", "master", "m.tech", "mtech",
                   "mba", "bsc", "msc", "phd", "doctorate", "diploma", "b.sc", "m.sc",
                   "bca", "mca"]


def _first_line_name(text: str) -> str | None:
    for line in text.splitlines():
        s = line.strip().lstrip("#").strip().lstrip("-*•").strip()
        if s and len(s) <= 60 and "@" not in s and not any(ch.isdigit() for ch in s):
            words = s.split()
            if 1 < len(words) <= 4 and all(w[:1].isupper() for w in words if w[:1].isalpha()):
                return s
    return None


def _extract_skills(sections: dict[str, str]) -> dict[str, list[str]]:
    from app.services.nlp_features import extract_skill_entities

    skill_blob = " ".join(
        [sections.get("skills", ""), sections.get("summary", "")]
    )
    lines = []
    for raw in re.split(r"[,\n;|/•·]", skill_blob):
        tok = raw.strip()
        if tok and len(tok) <= 40:
            lines.append(tok)
    canon = normalize_skills(lines + extract_skill_entities("\n".join(sections.values())))
    buckets: dict[str, list[str]] = {
        "technical_skills": [], "programming_languages": [], "frameworks": [],
        "databases": [], "cloud_technologies": [], "tools": [], "soft_skills": [],
    }
    for s in canon:
        cat = category_of(s)
        if cat == "programming_language":
            buckets["programming_languages"].append(s)
        elif cat == "framework":
            buckets["frameworks"].append(s)
        elif cat == "database":
            buckets["databases"].append(s)
        elif cat == "cloud":
            buckets["cloud_technologies"].append(s)
        elif cat == "tool":
            buckets["tools"].append(s)
        elif cat == "soft":
            buckets["soft_skills"].append(s)
        else:
            buckets["technical_skills"].append(s)
    return buckets


def _extract_education(sections: dict[str, str]) -> list[dict]:
    out: list[dict] = []
    for line in sections.get("education", "").splitlines():
        low = line.lower()
        if any(k in low for k in DEGREE_KEYWORDS) or YEAR_RE.search(line):
            years = [int(y) for y in YEAR_RE.findall(line)]
            out.append({
                "degree": line.strip()[:200] or None,
                "field_of_study": _guess_field(low),
                "institution": None,
                "end_year": years[-1] if years else None,
            })
    return out[:6]


def _guess_field(low: str) -> str | None:
    for f in ["computer science", "information technology", "electrical", "electronics",
              "mechanical", "data science", "artificial intelligence", "mathematics",
              "business", "commerce", "statistics"]:
        if f in low:
            return f.title()
    return None


def _extract_experience(sections: dict[str, str]) -> list[dict]:
    body = sections.get("experience", "")
    blocks = re.split(r"\n(?=\S.*(?:at |@|,|-)\s*[A-Z])", body)
    out: list[dict] = []
    for block in blocks:
        if not block.strip():
            continue
        dates = DATE_RANGE_RE.search(block)
        start = end = None
        is_current = False
        if dates:
            start, end = dates.group(1), dates.group(2)
            is_current = bool(end and end.lower().strip() in {"present", "current"})
        first = block.strip().splitlines()[0][:200]
        low = block.lower()
        if "intern" in low:
            kind = "internship"
        elif "freelance" in low:
            kind = "freelance"
        elif any(h in low for h in ("university", "college", "academic", "research assistant",
                                    "research associate", "coursework", "capstone", "thesis")):
            kind = "academic"
        else:
            kind = "full-time"
        out.append({
            "company": None,
            "title": first or None,
            "description": block.strip()[:1500],
            "start_date": start,
            "end_date": end,
            "is_current": is_current,
            "kind": kind,
        })
    return out[:10]


def _extract_projects(sections: dict[str, str]) -> list[dict]:
    body = sections.get("projects", "")
    out: list[dict] = []
    for block in re.split(r"\n\s*\n|(?=\n\S.*:\s*)", body):
        s = block.strip()
        if len(s) < 3:
            continue
        name = s.splitlines()[0][:160]
        techs = normalize_skills(re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{1,20}", s))
        out.append({"name": name, "description": s[:1200], "technologies": techs[:12]})
    return out[:10]


def _extract_certifications(sections: dict[str, str]) -> list[dict]:
    out = []
    for line in sections.get("certifications", "").splitlines():
        s = line.strip(" -•|")
        if len(s) > 2:
            years = YEAR_RE.findall(s)
            out.append({"name": s[:200], "issuer": None,
                        "year": int(years[-1]) if years else None})
    return out[:15]


def deterministic_structure(text: str) -> ResumeSchema:
    sections = detect_sections(text)
    contact_email = EMAIL_RE.search(text)
    contact_phone = PHONE_RE.search(text)
    sk = _extract_skills(sections)
    summary = sections.get("summary", "")[:1200] or None
    all_skills = normalize_skills(
        sk["technical_skills"] + sk["programming_languages"] + sk["frameworks"]
        + sk["databases"] + sk["cloud_technologies"] + sk["tools"]
    )
    data = {
        "candidate_name": _first_line_name(text),
        "contact": {
            "email": contact_email.group(0) if contact_email else None,
            "phone": contact_phone.group(0).strip() if contact_phone else None,
        },
        "summary": summary,
        "skills": all_skills,
        **sk,
        "education": _extract_education(sections),
        "experience": _extract_experience(sections),
        "projects": _extract_projects(sections),
        "certifications": _extract_certifications(sections),
        "languages": _extract_languages(text),
    }
    return ResumeSchema.model_validate(data)


def _extract_languages(text: str) -> list[str]:
    langs = ["english", "hindi", "spanish", "french", "german", "mandarin", "tamil",
             "telugu", "marathi", "bengali", "arabic", "japanese"]
    low = text.lower()
    return [l.title() for l in langs if l in low][:6]


def structure_resume(text: str, llm=None) -> dict:
    """Deterministic structure, optionally enriched by an LLM, then validated."""
    base = deterministic_structure(text)
    if llm is not None:
        try:
            from app.services.resume_parser.resume_structurer import _llm_merge

            base = _llm_merge(base, text, llm)
        except Exception as exc:  # pragma: no cover
            logger.warning("LLM enrichment skipped: %s", exc)
    return base.model_dump()


def _llm_merge(base: ResumeSchema, text: str, llm) -> ResumeSchema:
    """Merge LLM extraction without letting it contradict deterministic facts."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    import json

    from app.services.llm_service.prompts import resume_extraction_prompt

    prompt = resume_extraction_prompt(text)
    try:
        async def generate():
            return await llm.generate(prompt)

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            raw = asyncio.run(generate())
        else:
            # The upload API is async, while this parser intentionally keeps
            # a synchronous contract for workers and tests. Run only the
            # provider call in a helper thread when an event loop is active.
            with ThreadPoolExecutor(max_workers=1) as executor:
                raw = executor.submit(asyncio.run, generate()).result()
        parsed = json.loads(_strip_json(raw))
    except Exception:
        return base
    try:
        llm_schema = ResumeSchema.model_validate(parsed)
    except Exception:
        return base
    merged = base.model_copy(deep=True)
    # Only fill empty deterministic fields; never overwrite found facts.
    if not merged.candidate_name and llm_schema.candidate_name:
        merged.candidate_name = llm_schema.candidate_name
    if not merged.contact.email and llm_schema.contact.email:
        merged.contact.email = llm_schema.contact.email
    if not merged.contact.phone and llm_schema.contact.phone:
        merged.contact.phone = llm_schema.contact.phone
    if not merged.summary and llm_schema.summary:
        merged.summary = llm_schema.summary
    for field in (
        "skills", "technical_skills", "soft_skills", "programming_languages",
        "frameworks", "databases", "cloud_technologies", "tools", "languages",
    ):
        existing = set(getattr(merged, field))
        for value in getattr(llm_schema, field):
            if value not in existing:
                getattr(merged, field).append(value)
                existing.add(value)
    for field in ("education", "experience", "projects", "certifications"):
        if not getattr(merged, field) and getattr(llm_schema, field):
            setattr(merged, field, getattr(llm_schema, field))
    if not merged.total_experience_years and llm_schema.total_experience_years:
        merged.total_experience_years = llm_schema.total_experience_years
    return merged


def _strip_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        return raw[start:end + 1]
    return raw
