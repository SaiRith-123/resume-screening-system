"""Unit tests: fuzzy + contextual matching (spec §8)."""
from app.services.skill_matcher.matcher import CONTEXT_STRENGTH, Matcher


def _skills(**kwargs):
    return kwargs


def test_exact_match():
    cand = {"Python": {"context": "experience", "evidence": "Built APIs with Python."}}
    m = Matcher().match_one(cand, "Python")
    assert m.status == "MATCH"
    assert m.strategy == "exact"


def test_fuzzy_match_typo():
    cand = {"PostgreSQL": {"context": "skills"}}
    m = Matcher().match_one(cand, "PostgressQL")
    assert m.status in {"MATCH", "PARTIAL_MATCH"}


def test_related_partial_credit():
    cand = {"MySQL": {"context": "experience"}}
    m = Matcher().match_one(cand, "PostgreSQL")
    assert m.status in {"PARTIAL_MATCH", "MATCH"}
    assert m.strategy in {"related", "fuzzy", "semantic"}


def test_unrelated_is_missing():
    cand = {"Java": {"context": "experience"}}
    m = Matcher().match_one(cand, "Python")
    assert m.status == "MISSING"


def test_context_strength_ordering():
    assert CONTEXT_STRENGTH["experience"] > CONTEXT_STRENGTH["skills"]
    assert CONTEXT_STRENGTH["project"] > CONTEXT_STRENGTH["skills"]


def test_contextual_confidence_uses_stronger_context():
    weak = {"Python": {"context": "skills"}}
    strong = {"Python": {"context": "experience"}}
    mw = Matcher().match_one(weak, "Python")
    ms = Matcher().match_one(strong, "Python")
    assert ms.confidence >= mw.confidence
