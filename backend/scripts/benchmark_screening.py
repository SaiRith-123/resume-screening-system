"""Benchmark automated screening against a measured manual-review baseline.

Run from ``backend``:
    python scripts/benchmark_screening.py --candidates 100 --manual-minutes 5

The manual baseline is deliberately explicit. Replace it with an observed
recruiter average for a defensible productivity claim; this script does not
pretend to measure human time by simulating a person.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.db.base import Base  # noqa: E402
from app.models import Candidate, Job, User  # noqa: E402,F401
from app.repositories.candidate_repo import CandidateRepository  # noqa: E402
from app.repositories.job_repo import JobRepository  # noqa: E402
from app.repositories.user_repo import UserRepository  # noqa: E402
from app.services.embedding_service.embedder import Embedder  # noqa: E402
from app.services.resume_parser.resume_structurer import deterministic_structure  # noqa: E402
from app.services.screening.pipeline import run_screening  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=int, default=100)
    parser.add_argument("--manual-minutes", type=float, default=5.0)
    parser.add_argument("--target-reduction", type=float, default=80.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.candidates < 1 or args.manual_minutes <= 0:
        raise SystemExit("candidates must be positive and manual-minutes must be greater than zero")

    resume_paths = sorted((ROOT / "sample_data" / "resumes").glob("*.md"))
    if not resume_paths:
        raise SystemExit("No sample resumes found")
    profiles = [deterministic_structure(path.read_text(encoding="utf-8")) for path in resume_paths]

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        user = UserRepository.create(session, "benchmark@example.com", "Benchmark", "password123")
        job = JobRepository.create(
            session,
            user.id,
            {
                "title": "Benchmark Software Engineer",
                "description": "Python backend engineer with SQL and API development experience.",
                "hard_gate": False,
            },
            [
                {"kind": "skill", "priority": "required", "value": "Python"},
                {"kind": "skill", "priority": "required", "value": "SQL"},
                {"kind": "skill", "priority": "preferred", "value": "Docker"},
            ],
        )
        for index in range(args.candidates):
            profile = profiles[index % len(profiles)]
            candidate = CandidateRepository.create(session, job.id, name=profile.candidate_name)
            candidate.structured = profile.model_dump()
            candidate.total_experience_years = profile.total_experience_years
            candidate.status = "ANALYZED"
            session.commit()

        manual_seconds = args.candidates * args.manual_minutes * 60
        # Explicit low-dimensional hashing keeps this performance run offline and repeatable.
        embedder = Embedder(dim=256)
        started = time.perf_counter()
        results = run_screening(session, job.id, embedder=embedder)
        automated_seconds = time.perf_counter() - started
        reduction = (1 - automated_seconds / manual_seconds) * 100
        report = {
            "candidates": args.candidates,
            "source_profiles": len(profiles),
            "manual_baseline_minutes": args.manual_minutes,
            "manual_baseline_seconds": round(manual_seconds, 3),
            "automated_seconds": round(automated_seconds, 3),
            "screened": len(results),
            "ranked": sum(result.rank is not None for result in results),
            "time_reduction_percent": round(reduction, 2),
            "target_reduction_percent": args.target_reduction,
            "target_met": reduction >= args.target_reduction,
        }
        print(json.dumps(report, indent=2))
        return 0 if report["target_met"] else 1
    finally:
        session.close()
        Base.metadata.drop_all(engine)


if __name__ == "__main__":
    raise SystemExit(main())