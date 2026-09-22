"""Compare degraded hash and real transformer semantic scores on sample data."""
from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.embedding_service.embedder import Embedder  # noqa: E402
from app.services.resume_parser.resume_structurer import deterministic_structure  # noqa: E402
from app.services.scoring_engine.scorer import semantic_score  # noqa: E402
from app.services.screening.pipeline import _candidate_corpus, _semantic_similarity  # noqa: E402


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def main() -> None:
    resume_paths = sorted((ROOT / "sample_data" / "resumes").glob("*.md"))
    job_paths = sorted((ROOT / "sample_data" / "job_descriptions").glob("*.md"))
    hash_embedder = Embedder(backend="hash", dim=384)
    real_embedder = Embedder(cache_dir=str(ROOT / ".cache" / "embeddings"))
    commit = git_commit()
    rows = []
    for resume_path in resume_paths:
        structured = deterministic_structure(resume_path.read_text(encoding="utf-8"))
        candidate_text = _candidate_corpus(structured.model_dump())
        for job_path in job_paths:
            job_text = job_path.read_text(encoding="utf-8")
            hash_similarity = _semantic_similarity(candidate_text, job_text, hash_embedder)
            real_similarity = _semantic_similarity(candidate_text, job_text, real_embedder)
            rows.append({
                "resume": resume_path.name,
                "job": job_path.name,
                "hash_semantic_score": semantic_score(hash_similarity),
                "real_semantic_score": semantic_score(real_similarity),
                "delta": round(semantic_score(real_similarity) - semantic_score(hash_similarity), 1),
            })
    real_scores = [row["real_semantic_score"] for row in rows]
    hash_scores = [row["hash_semantic_score"] for row in rows]
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "git_commit_status": "recorded" if commit else "no_commit_exists",
        "dataset": {"resumes": len(resume_paths), "jobs": len(job_paths), "comparisons": len(rows)},
        "models": {
            "degraded": {"backend": "hash", "dimension": 384},
            "real": {
                "backend": real_embedder.backend,
                "name": real_embedder.model_name,
                "dimension": real_embedder.dim,
                "sentence_transformers_version": package_version("sentence-transformers"),
            },
        },
        "aggregate": {
            "mean_hash_semantic_score": round(sum(hash_scores) / len(hash_scores), 2),
            "mean_real_semantic_score": round(sum(real_scores) / len(real_scores), 2),
            "mean_delta": round(sum(row["delta"] for row in rows) / len(rows), 2),
        },
        "comparisons": rows,
    }
    output = ROOT / "results" / "phase1_embedding_comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), **result["dataset"], **result["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()