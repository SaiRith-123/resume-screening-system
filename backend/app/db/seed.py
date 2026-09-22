"""Seed a demo account, sample jobs and sample candidates (spec §25).

Run:  python -m app.db.seed
Reads job descriptions and resumes from ``sample_data/`` next to the backend
(or one level up), ingests the resumes, and screens every candidate.
"""
from __future__ import annotations

import os

from app.core.logging import get_logger

logger = get_logger(__name__)

DEMO_EMAIL = "demo@recruiter.io"
DEMO_PASSWORD = "demo12345"


def _find_sample_dir() -> str | None:
    candidates = [
        os.environ.get("SAMPLE_DATA_DIR", ""),
        os.path.join(os.getcwd(), "sample_data"),
        os.path.join(os.getcwd(), "..", "sample_data"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "sample_data"),
    ]
    for path in candidates:
        if path and os.path.isdir(os.path.join(path, "job_descriptions")):
            return os.path.abspath(path)
    return None


def seed(force: bool = False) -> dict:
    from app.db.init_db import init_db
    from app.db.session import new_session
    from app.models.candidate import Resume
    from app.models.user import User
    from app.repositories.candidate_repo import CandidateRepository
    from app.repositories.job_repo import JobRepository
    from app.repositories.user_repo import UserRepository
    from app.services.processing import ingest_resume
    from app.services.screening.pipeline import run_screening

    init_db()
    db = new_session()
    summary = {"jobs": 0, "candidates": 0, "screened": 0}
    try:
        user = UserRepository.get_by_email(db, DEMO_EMAIL)
        if user is None:
            user = UserRepository.create(db, DEMO_EMAIL, "Demo Recruiter", DEMO_PASSWORD)

        sample_dir = _find_sample_dir()
        if sample_dir is None:
            logger.warning("sample_data/ not found; created demo user only.")
            return {"jobs": 0, "candidates": 0, "screened": 0, "user": DEMO_EMAIL}

        jd_dir = os.path.join(sample_dir, "job_descriptions")
        resume_dir = os.path.join(sample_dir, "resumes")
        jd_files = sorted(f for f in os.listdir(jd_dir) if f.endswith((".md", ".txt")))

        existing = {j.title for j in JobRepository.list_for_owner(db, user.id)}
        for jd in jd_files:
            with open(os.path.join(jd_dir, jd), encoding="utf-8") as fh:
                content = fh.read()
            title = _title_of(content, jd)
            if title in existing and not force:
                continue
            reqs = _requirements_from_content(content)
            job = JobRepository.create(
                db, user.id,
                {"title": title, "description": content, "weights": {},
                 "hard_gate": False},
                reqs,
            )
            summary["jobs"] += 1

            # attach the matching sample resumes (filename prefix convention: profile only)
            if not os.path.isdir(resume_dir):
                continue
            for rf in sorted(os.listdir(resume_dir)):
                if not rf.endswith((".md", ".txt")):
                    continue
                with open(os.path.join(resume_dir, rf), encoding="utf-8") as fh:
                    rtext = fh.read()
                cand = CandidateRepository.create(db, job.id)
                resume_path = os.path.join(resume_dir, rf)
                import hashlib

                digest = hashlib.sha256(rtext.encode("utf-8")).hexdigest()
                CandidateRepository.add_resume(
                    db, cand.id, original_filename=rf, stored_path=resume_path,
                    content_type="text/markdown", size_bytes=len(rtext.encode("utf-8")),
                    sha256=digest,
                )
                ingest_resume(db, cand, cand.resumes[0])
                summary["candidates"] += 1
            run_screening(db, job.id)
            summary["screened"] += len(JobRepository.list_for_owner(db, user.id)) and 1 or 0
        summary["user"] = DEMO_EMAIL
        return summary
    finally:
        db.close()


def _title_of(content: str, filename: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()[:120]
        if line:
            return line[:120]
    return filename.rsplit(".", 1)[0]


def _requirements_from_content(content: str) -> list[dict]:
    from app.services.jd_parser.jd_structurer import deterministic_jd

    parsed = deterministic_jd(content)
    reqs: list[dict] = []
    for s in parsed.required_skills:
        reqs.append({"kind": "skill", "priority": "required", "value": s})
    for s in parsed.preferred_skills:
        reqs.append({"kind": "skill", "priority": "preferred", "value": s})
    if parsed.minimum_experience_years:
        reqs.append({"kind": "experience", "priority": "required",
                     "value": "minimum experience",
                     "min_years": parsed.minimum_experience_years})
    for e in parsed.education:
        reqs.append({"kind": "education", "priority": "required", "value": e})
    return reqs


def main() -> None:
    result = seed()
    logger.info("Seed complete: %s", result)
    print(f"Seed complete: {result}")
    if result.get("user"):
        print(f"Demo login -> email: {DEMO_EMAIL}  password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
