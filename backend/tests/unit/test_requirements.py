"""Unit tests: JD parsing + requirement classification (spec §6, §9, §12)."""
from app.services.jd_parser.jd_structurer import deterministic_jd
from app.services.scoring_engine.education import match_education

JD = """# Machine Learning Engineer
## Requirements
- 2+ years of experience
- Python
- SQL
- Machine Learning
- Bachelor's degree in Computer Science
## Preferred
- PyTorch
- AWS
## Responsibilities
- Develop machine learning models
- Build production ML pipelines
"""


def test_required_and_preferred_split():
    parsed = deterministic_jd(JD)
    assert "Python" in parsed.required_skills
    assert "Machine Learning" in parsed.required_skills
    assert "PyTorch" in parsed.preferred_skills
    assert "AWS" in parsed.preferred_skills


def test_required_skills_never_in_preferred():
    parsed = deterministic_jd(JD)
    assert not (set(parsed.required_skills) & set(parsed.preferred_skills))


def test_responsibilities_extracted_separately():
    parsed = deterministic_jd(JD)
    assert any("models" in r.lower() for r in parsed.responsibilities)


def test_minimum_experience_parsed():
    parsed = deterministic_jd(JD)
    assert parsed.minimum_experience_years == 2.0


def test_education_required_parsed():
    parsed = deterministic_jd(JD)
    assert any("bachelor" in e.lower() for e in parsed.education)


def test_education_match_synonyms():
    status, score = match_education(
        [{"degree": "B.Tech Computer Science"}],
        ["Bachelor's degree in Computer Science"],
    )
    assert status == "MATCH"
    assert score >= 90


def test_education_missing():
    status, score = match_education([], ["Bachelor's degree in Computer Science"])
    assert status == "MISSING"
    assert score == 0.0


def test_higher_degree_satisfies_lower_requirement():
    status, _ = match_education(
        [{"degree": "M.Tech Computer Science"}],
        ["Bachelor's degree in Computer Science"],
    )
    assert status == "MATCH"
