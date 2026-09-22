"""Unit tests: experience calculation (spec §11)."""
from app.services.scoring_engine.experience import (
    experience_intervals,
    experience_score,
    total_experience_years,
)


def test_simple_duration():
    exps = [{"start_date": "2020", "end_date": "2022", "kind": "full-time"}]
    assert total_experience_years(exps) == 2.0


def test_overlapping_jobs_are_not_double_counted():
    exps = [
        {"start_date": "2020-01", "end_date": "2022-01", "kind": "full-time"},
        {"start_date": "2021-01", "end_date": "2023-01", "kind": "full-time"},
    ]
    # union is 2020-01 .. 2023-01 -> 36 months -> 3 years, not 4
    assert total_experience_years(exps) == 3.0


def test_academic_projects_excluded():
    exps = [
        {"start_date": "2020-01", "end_date": "2022-01", "kind": "full-time"},
        {"start_date": "2019-01", "end_date": "2020-01", "kind": "academic",
         "description": "University capstone project"},
    ]
    assert total_experience_years(exps) == 2.0


def test_current_employment_uses_today():
    from datetime import date

    exps = [{"start_date": "2020-01", "end_date": None, "is_current": True, "kind": "full-time"}]
    years = total_experience_years(exps)
    expected = round(((date.today().year - 2020) * 12 + date.today().month - 1) / 12, 1)
    assert abs(years - expected) < 0.2


def test_missing_dates_ignored():
    exps = [{"company": "X", "title": "Dev", "kind": "full-time"}]
    assert total_experience_years(exps) == 0.0


def test_internship_counts_but_academic_does_not():
    exps = [
        {"start_date": "2023-01", "end_date": "2023-07", "kind": "internship"},
        {"start_date": "2023-01", "end_date": "2023-07", "kind": "academic"},
    ]
    assert total_experience_years(exps) == 0.5


def test_experience_score_partial_credit():
    assert experience_score(4, 2) == 100.0
    assert 80 < experience_score(2, 2) <= 100
    assert experience_score(0, 3) == 0.0
    assert 0 < experience_score(1.5, 3) < 100
