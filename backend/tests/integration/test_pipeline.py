"""Integration test: Upload -> Extract -> Parse -> Match -> Score -> Rank (spec §24).

Exercises the real scoring/matching pipeline end to end on structured candidates
built from realistic resume JSON. Verifies that ranking behaves sensibly.
"""
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.user_repo import UserRepository
from app.services.screening.pipeline import run_screening

JOB = {
    "title": "Machine Learning Engineer",
    "description": "Python, SQL, Machine Learning. 2+ years. Bachelor's degree.",
    "weights": {},
    "hard_gate": True,
}
REQS = [
    {"kind": "skill", "priority": "required", "value": "Python", "is_hard_gate": True},
    {"kind": "skill", "priority": "required", "value": "SQL"},
    {"kind": "skill", "priority": "required", "value": "Machine Learning"},
    {"kind": "skill", "priority": "preferred", "value": "PyTorch"},
    {"kind": "experience", "priority": "required", "value": "experience",
     "min_years": 2, "is_hard_gate": True},
    {"kind": "education", "priority": "required",
     "value": "Bachelor's degree in Computer Science"},
]

EXCELLENT = {
    "candidate_name": "Excellent Candidate",
    "summary": "ML engineer with 4 years building ML systems in Python.",
    "skills": ["Python", "SQL", "Machine Learning", "PyTorch", "Docker"],
    "experience": [{"title": "ML Engineer", "company": "BigCo",
                    "description": "Built ML models with Python and PyTorch.",
                    "start_date": "2021", "end_date": "2025", "kind": "full-time"}],
    "projects": [{"name": "Ranking Model", "description": "ML ranking with Python",
                  "technologies": ["Python", "PyTorch"]}],
    "education": [{"degree": "B.Tech Computer Science"}],
    "certifications": [],
}
POOR = {
    "candidate_name": "Poor Candidate",
    "summary": "Marketing specialist.",
    "skills": ["Marketing", "Excel", "Communication"],
    "experience": [{"title": "Marketing Exec", "company": "AdCo",
                    "description": "Ran campaigns.",
                    "start_date": "2019", "end_date": "2025", "kind": "full-time"}],
    "projects": [],
    "education": [{"degree": "MBA Marketing"}],
    "certifications": [],
}
MISSING_MANDATORY = {
    "candidate_name": "Java Only",
    "summary": "Java backend developer, no ML experience.",
    "skills": ["Java", "Spring", "MySQL"],
    "experience": [{"title": "Java Dev", "company": "X", "description": "Java APIs.",
                    "start_date": "2020", "end_date": "2025", "kind": "full-time"}],
    "projects": [],
    "education": [{"degree": "B.Tech Information Technology"}],
    "certifications": [],
}


def _seed(db):
    user = UserRepository.create(db, "seed@x.com", "Seed", "password123")
    job = JobRepository.create(db, user.id, JOB, REQS)
    ids = {}
    for name, structured in (("excellent", EXCELLENT), ("poor", POOR),
                             ("java", MISSING_MANDATORY)):
        cand = CandidateRepository.create(db, job.id, name=structured["candidate_name"])
        cand.structured = structured
        from app.services.scoring_engine.experience import total_experience_years

        cand.total_experience_years = total_experience_years(structured["experience"])
        db.commit()
        ids[name] = cand.id
    return user, job, ids


def test_pipeline_ranks_excellent_above_poor(db_session):
    _, job, ids = _seed(db_session)
    results = run_screening(db_session, job.id)
    assert len(results) == 3

    by_id = {r.candidate_id: r for r in results}
    assert by_id[ids["excellent"]].final_score > by_id[ids["poor"]].final_score
    assert by_id[ids["excellent"]].rank == 1
    # excellent should clear the mandatory gate
    assert by_id[ids["excellent"]].eligibility_status == "MEETS_ALL_MANDATORY"


def test_missing_mandatory_is_flagged_not_dropped(db_session):
    _, job, ids = _seed(db_session)
    run_screening(db_session, job.id)
    from app.repositories.screening_repo import ScreeningRepository

    res = ScreeningRepository.get_for_candidate(db_session, job.id, ids["java"])
    assert res is not None  # never silently rejected
    assert res.eligibility_status in {"DOES_NOT_MEET_MANDATORY", "MISSING_REQUIREMENTS"}
    assert res.needs_review is True
    assert res.final_score < 100


def test_all_component_scores_persisted(db_session):
    _, job, ids = _seed(db_session)
    run_screening(db_session, job.id)
    from app.repositories.screening_repo import ScreeningRepository

    res = ScreeningRepository.get_for_candidate(db_session, job.id, ids["excellent"])
    for attr in ("skill_score", "experience_score", "semantic_score", "education_score",
                 "project_score", "certification_score", "preferred_score"):
        assert getattr(res, attr) is not None


def test_evidence_is_grounded(db_session):
    _, job, ids = _seed(db_session)
    run_screening(db_session, job.id)
    from app.repositories.screening_repo import ScreeningRepository

    res = ScreeningRepository.get_for_candidate(db_session, job.id, ids["excellent"])
    # at least one evidence row should carry a real snippet
    assert any(e.evidence_text for e in res.evidence)
