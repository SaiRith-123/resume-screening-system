"""Multi-strategy skill matcher (spec §8, §9, §13).

Strategies:
  A. exact      - normalized equality
  B. fuzzy      - RapidFuzz token ratio over raw/normalized names
  C. semantic   - cosine similarity of sentence embeddings
  D. contextual - evidence strength depends on WHERE a skill appears
"""
from __future__ import annotations

from dataclasses import dataclass, field

try:
    from rapidfuzz import fuzz

    _HAS_RAPIDFUZZ = True
except Exception:  # pragma: no cover
    _HAS_RAPIDFUZZ = False
    import difflib

from app.schemas.common import MatchStatus
from app.services.skill_matcher.normalizer import normalize_skill
from app.services.skill_matcher.taxonomy import relatedness

# Contextual evidence strength by source section (spec §8D)
CONTEXT_STRENGTH: dict[str, float] = {
    "experience": 1.0,
    "project": 0.85,
    "certification": 0.7,
    "summary": 0.6,
    "skills": 0.5,
    "list": 0.5,
    "unknown": 0.3,
}

# threshold bands
EXACT_THRESHOLD = 1.0
FUZZY_MATCH = 88.0
FUZZY_PARTIAL = 74.0
SEMANTIC_MATCH = 0.72
SEMANTIC_PARTIAL = 0.55


@dataclass
class SkillMatch:
    skill: str
    status: str
    confidence: float = 0.0
    strategy: str = "exact"
    context: str = "list"
    evidence: str | None = None
    matched_to: str | None = None
    relatedness: float = 0.0
    extra: dict = field(default_factory=dict)


def _fuzzy_ratio(a: str, b: str) -> float:
    if _HAS_RAPIDFUZZ:
        return float(fuzz.token_set_ratio(a, b))
    return difflib.SequenceMatcher(None, a, b).ratio() * 100.0


class Matcher:
    """Stateless matcher over a candidate's normalized skills."""

    def __init__(self, embedder=None):
        self.embedder = embedder

    # --- A. exact -----------------------------------------------------------
    @staticmethod
    def exact(candidate_skills: dict[str, dict], required: str) -> SkillMatch | None:
        canon = normalize_skill(required)
        if canon in candidate_skills:
            ctx = candidate_skills[canon].get("context", "list")
            return SkillMatch(
                skill=canon,
                status=MatchStatus.MATCH.value,
                confidence=1.0,
                strategy="exact",
                context=ctx,
                evidence=candidate_skills[canon].get("evidence"),
                matched_to=canon,
                relatedness=1.0,
            )
        return None

    # --- B. fuzzy -----------------------------------------------------------
    @staticmethod
    def fuzzy(candidate_skills: dict[str, dict], required: str) -> SkillMatch | None:
        canon = normalize_skill(required)
        best: SkillMatch | None = None
        for cand, meta in candidate_skills.items():
            ratio = _fuzzy_ratio(canon.lower(), cand.lower())
            if ratio >= FUZZY_MATCH:
                m = SkillMatch(
                    skill=canon,
                    status=MatchStatus.MATCH.value,
                    confidence=round(ratio / 100.0 * 0.9, 3),
                    strategy="fuzzy",
                    context=meta.get("context", "list"),
                    evidence=meta.get("evidence"),
                    matched_to=cand,
                    relatedness=1.0,
                )
            elif ratio >= FUZZY_PARTIAL:
                m = SkillMatch(
                    skill=canon,
                    status=MatchStatus.PARTIAL_MATCH.value,
                    confidence=round(ratio / 100.0 * 0.75, 3),
                    strategy="fuzzy",
                    context=meta.get("context", "list"),
                    evidence=meta.get("evidence"),
                    matched_to=cand,
                    relatedness=round(ratio / 100.0, 3),
                )
            else:
                continue
            if best is None or m.confidence > best.confidence:
                best = m
        return best

    # --- C. semantic --------------------------------------------------------
    def semantic(self, candidate_skills: dict[str, dict], required: str) -> SkillMatch | None:
        if self.embedder is None or not candidate_skills:
            return None
        names = list(candidate_skills.keys())
        try:
            vecs = self.embedder.encode([required] + names)
        except Exception:
            return None
        target = vecs[0]
        best_sim = -1.0
        best_name = None
        for i, name in enumerate(names, start=1):
            sim = self.embedder.similarity(target, vecs[i])
            if sim > best_sim:
                best_sim = sim
                best_name = name
        if best_name is None:
            return None
        meta = candidate_skills[best_name]
        if best_sim >= SEMANTIC_MATCH:
            status, conf = MatchStatus.MATCH.value, round(best_sim, 3)
        elif best_sim >= SEMANTIC_PARTIAL:
            status, conf = MatchStatus.PARTIAL_MATCH.value, round(best_sim * 0.85, 3)
        else:
            return None
        return SkillMatch(
            skill=normalize_skill(required),
            status=status,
            confidence=conf,
            strategy="semantic",
            context=meta.get("context", "list"),
            evidence=meta.get("evidence"),
            matched_to=best_name,
            relatedness=round(best_sim, 3),
        )

    # --- D. related (taxonomy partial credit) -------------------------------
    @staticmethod
    def related(candidate_skills: dict[str, dict], required: str) -> SkillMatch | None:
        canon = normalize_skill(required)
        best: SkillMatch | None = None
        for cand, meta in candidate_skills.items():
            rel = relatedness(canon, cand)
            if rel > 0 and cand != canon:
                m = SkillMatch(
                    skill=canon,
                    status=(
                        MatchStatus.PARTIAL_MATCH.value if rel >= 0.4 else MatchStatus.MISSING.value
                    ),
                    confidence=round(rel * 0.7, 3),
                    strategy="related",
                    context=meta.get("context", "list"),
                    evidence=meta.get("evidence"),
                    matched_to=cand,
                    relatedness=rel,
                )
                if best is None or m.confidence > best.confidence:
                    best = m
        return best if (best and best.confidence > 0) else None

    # --- orchestrating matcher ---------------------------------------------
    def match_one(self, candidate_skills: dict[str, dict], required: str) -> SkillMatch:
        for strategy in (self.exact, self.fuzzy, self.semantic, self.related):
            m = strategy(candidate_skills, required)  # type: ignore[arg-type]
            if m is not None:
                m.confidence = _apply_context(m.confidence, m.context)
                return m
        return SkillMatch(
            skill=normalize_skill(required),
            status=MatchStatus.MISSING.value,
            confidence=0.0,
            strategy="none",
            context="unknown",
        )

    def match_many(
        self, candidate_skills: dict[str, dict], requirements: list[str]
    ) -> list[SkillMatch]:
        return [self.match_one(candidate_skills, r) for r in requirements]

    def match_all(
        self,
        candidate_texts: dict[str, str],
        candidate_skills: dict[str, dict],
        required: list[str],
        preferred: list[str] | None = None,
    ) -> dict[str, list[SkillMatch]]:
        """Convenience entry point returning required + preferred matches."""
        return {
            "required": self.match_many(candidate_skills, required),
            "preferred": self.match_many(candidate_skills, preferred or []),
        }


def _apply_context(confidence: float, context: str) -> float:
    """Weight confidence by evidence context so listed skills count less (spec §8D)."""
    strength = CONTEXT_STRENGTH.get(context, 0.5)
    return round(min(1.0, confidence * (0.6 + 0.4 * strength)), 3)
