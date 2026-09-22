"""Unit tests: scoring engine (spec §10, §26)."""
import pytest

from app.services.scoring_engine.scorer import (
    certification_score,
    component_scores,
    final_score,
    semantic_score,
    skill_score,
)
from app.services.scoring_engine.weights import DEFAULT_WEIGHTS, normalize_weights


class _M:
    def __init__(self, status, confidence=1.0):
        self.status = status
        self.confidence = confidence


def test_default_weights_match_spec():
    assert DEFAULT_WEIGHTS == {
        "skill": 0.35, "experience": 0.20, "semantic": 0.15, "education": 0.10,
        "project": 0.10, "certification": 0.05, "preferred": 0.05,
    }
    assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9


def test_weights_normalize_to_one():
    w = normalize_weights({"skill": 2, "experience": 2})
    assert abs(sum(w.values()) - 1.0) < 1e-4


def test_final_score_is_weighted_sum():
    components = {k: 100.0 for k in DEFAULT_WEIGHTS}
    assert final_score(components, DEFAULT_WEIGHTS) == 100.0
    components2 = {k: 0.0 for k in DEFAULT_WEIGHTS}
    assert final_score(components2, DEFAULT_WEIGHTS) == 0.0


def test_skill_score_all_matched_is_100():
    assert skill_score([_M("MATCH")] * 5) == 100.0


def test_skill_score_missing_is_zero():
    assert skill_score([_M("MISSING")] * 3) == 0.0


def test_skill_score_partial_between():
    score = skill_score([_M("MATCH"), _M("MISSING")])
    assert 0 < score < 100


def test_semantic_score_stretches_baseline():
    assert semantic_score(1.0) == 100.0
    assert semantic_score(0.0) == 0.0
    assert semantic_score(0.25) < 5.0


def test_certification_score():
    assert certification_score([], []) == 100.0
    assert certification_score([{"name": "AWS Certified"}], ["AWS Certified"]) == 100.0
    assert certification_score([{"name": "Something"}], ["AWS Certified"]) == 0.0


def test_component_scores_full_shape():
    comps = component_scores(
        required_matches=[_M("MATCH"), _M("MISSING")],
        preferred_matches=[_M("MATCH")],
        candidate_years=3,
        min_years=2,
        semantic_similarity=0.8,
        candidate_education=[{"degree": "B.Tech Computer Science"}],
        required_education=["Bachelor's degree in Computer Science"],
        candidate_certifications=[],
        required_certifications=[],
        project_relevance=0.7,
        n_projects=2,
    )
    assert set(comps) == set(DEFAULT_WEIGHTS)
    assert all(0.0 <= v <= 100.0 for v in comps.values())
    assert comps["education"] == 100.0
