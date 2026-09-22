"""Candidate ranking + eligibility gating (spec §9, §10).

A candidate missing a truly mandatory (hard-gate) requirement is flagged and
down-weighted but NEVER silently rejected - recruiters always see them.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Rankable:
    candidate_id: int
    final_score: float
    eligibility_status: str
    missing_hard_requirements: list[str]


def rank_candidates(items: list[Rankable]) -> list[Rankable]:
    """Sort by eligibility then score (non-gated first), preserving ties stably."""
    def key(it: Rankable):
        gated = 1 if (it.eligibility_status == "DOES_NOT_MEET_MANDATORY") else 0
        return (gated, -it.final_score, it.candidate_id)

    ordered = sorted(items, key=key)
    return ordered


def eligibility_status(missing_hard: list[str], missing_required: list[str],
                       hard_gate_enabled: bool) -> str:
    if missing_hard:
        return "DOES_NOT_MEET_MANDATORY" if hard_gate_enabled else "MISSING_REQUIREMENTS"
    if missing_required:
        return "MISSING_REQUIREMENTS"
    return "MEETS_ALL_MANDATORY"


def recommendation(score: float, eligibility: str, needs_review: bool) -> str:
    if eligibility == "DOES_NOT_MEET_MANDATORY":
        return "review" if needs_review else "not_eligible"
    if score >= 85:
        return "strong_match"
    if score >= 70:
        return "good_match"
    if score >= 55:
        return "possible_match"
    return "weak_match"
