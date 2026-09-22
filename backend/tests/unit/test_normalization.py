"""Unit tests: skill normalization + taxonomy relatedness (spec §7)."""
from app.services.skill_matcher.normalizer import normalize_skill, normalize_skills
from app.services.skill_matcher.taxonomy import relatedness


def test_aliases_map_to_canonical():
    assert normalize_skill("Postgres") == "PostgreSQL"
    assert normalize_skill("ReactJS") == "React"
    assert normalize_skill("Node") == "Node.js"
    assert normalize_skill("JS") == "JavaScript"
    assert normalize_skill("PyTorch framework") == "PyTorch"
    assert normalize_skill("REST API development") == "REST APIs"


def test_normalize_dedupes_and_preserves_order():
    result = normalize_skills(["Node", "Node.JS", "python", "PYTHON"])
    assert result[0] == "Node.js"
    assert result.count("Python") == 1


def test_unrelated_skills_are_not_identical():
    assert relatedness("Python", "Java") < 0.2
    assert relatedness("React", "Angular") < 0.5
    assert relatedness("PostgreSQL", "MongoDB") < 0.5
    assert relatedness("AWS", "Azure") < 0.5


def test_related_skills_get_partial_credit():
    assert relatedness("PostgreSQL", "MySQL") > 0.3
    assert relatedness("PyTorch", "TensorFlow") > 0.3
    assert relatedness("AWS", "GCP") > 0.3


def test_identical_skill_is_full():
    assert relatedness("Python", "Python") == 1.0
