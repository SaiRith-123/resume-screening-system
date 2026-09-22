"""Deterministic, transparent scoring engine (spec §10, §26).

The LLM never invents the final score. Every component is computed here, stored
separately, and combined with configurable weights.
"""
from __future__ import annotations

from app.services.scoring_engine.education import match_education
from app.services.scoring_engine.experience import experience_score
from app.services.scoring_engine.weights import DEFAULT_WEIGHTS, normalize_weights

STATUS_CREDIT = {"MATCH": 1.0, "PARTIAL_MATCH": 0.55, "MISSING": 0.0, "UNKNOWN": 0.35}


def _match_credit(match) -> float:
    status = getattr(match, "status", "MISSING")
    conf = getattr(match, "confidence", 0.0) or 0.0
    base = STATUS_CREDIT.get(status, 0.0)
    if status == "MATCH":
        return max(base, min(1.0, 0.7 + 0.3 * conf))
    if status == "PARTIAL_MATCH":
        return base * (0.6 + 0.4 * conf)
    if status == "UNKNOWN":
        return base
    return 0.0


def _ratio_score(matches: list) -> float:
    if not matches:
        return 100.0
    return round(sum(_match_credit(m) for m in matches) / len(matches) * 100.0, 1)


def skill_score(required_matches: list) -> float:
    return _ratio_score(required_matches)


def preferred_score(preferred_matches: list) -> float:
    if not preferred_matches:
        return 100.0
    return _ratio_score(preferred_matches)


def certification_score(candidate_certs: list[dict], required_certs: list[str]) -> float:
    if not required_certs:
        # no requirement -> neutral, but reward having any certs slightly
        return 100.0 if not candidate_certs else 90.0
    have = " ".join(
        f"{c.get('name', '')} {c.get('issuer', '')}".lower() for c in candidate_certs or []
    )
    hits = 0
    for req in required_certs:
        token = str(req).lower().split()[0] if str(req).split() else str(req).lower()
        if token and token in have:
            hits += 1
    return round(hits / len(required_certs) * 100.0, 1)


def semantic_score(similarity: float) -> float:
    """Map a cosine similarity (roughly 0..1) into 0..100 (spec §8C)."""
    sim = max(0.0, min(1.0, float(similarity)))
    # stretch around a 0.35 baseline so unrelated text is not over-credited
    stretched = max(0.0, (sim - 0.25) / 0.75)
    return round(min(1.0, stretched) * 100.0, 1)


def project_score(project_relevance: float, n_projects: int = 0) -> float:
    if n_projects == 0:
        return 0.0
    return round(max(0.0, min(1.0, project_relevance)) * 100.0, 1)


def component_scores(
    *,
    required_matches: list,
    preferred_matches: list,
    candidate_years: float,
    min_years: float | None,
    preferred_years: float | None = None,
    semantic_similarity: float = 0.0,
    candidate_education: list[dict] | None = None,
    required_education: list[str] | None = None,
    candidate_certifications: list[dict] | None = None,
    required_certifications: list[str] | None = None,
    project_relevance: float = 0.0,
    n_projects: int = 0,
) -> dict[str, float]:
    """Compute all seven 0..100 component scores (spec §10)."""
    _, edu_val = match_education(candidate_education or [], required_education or [])
    return {
        "skill": skill_score(required_matches),
        "experience": experience_score(candidate_years, min_years, preferred_years),
        "semantic": semantic_score(semantic_similarity),
        "education": edu_val,
        "project": project_score(project_relevance, n_projects),
        "certification": certification_score(
            candidate_certifications or [], required_certifications or []
        ),
        "preferred": preferred_score(preferred_matches),
    }


def final_score(components: dict[str, float], weights: dict[str, float] | None = None) -> float:
    """Weighted sum, with weights normalized to 1.0 (spec §10)."""
    w = normalize_weights(weights)
    total = 0.0
    for key, weight in w.items():
        total += float(components.get(key, 0.0)) * weight
    return round(total, 1)


__all__ = [
    "DEFAULT_WEIGHTS",
    "component_scores",
    "final_score",
    "skill_score",
    "preferred_score",
    "certification_score",
    "semantic_score",
    "project_score",
    "normalize_weights",
]
