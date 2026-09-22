"""Recruiter search endpoints (spec §27) - keyword + semantic candidate search."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.user import User
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.screening_repo import ScreeningRepository

router = APIRouter(prefix="/search", tags=["search"])


def _candidate_blob(cand: Candidate) -> str:
    s = cand.structured or {}
    parts = [cand.name or "", s.get("summary") or ""]
    parts += [str(x) for x in (s.get("skills") or [])]
    for exp in s.get("experience") or []:
        parts.append(" ".join(str(exp.get(k, "")) for k in ("title", "company", "description")))
    for proj in s.get("projects") or []:
        parts.append(" ".join(str(proj.get(k, "")) for k in ("name", "description")))
    return "\n".join(p for p in parts if p)


@router.get("/candidates")
def search_candidates(
    q: str | None = Query(None, description="Keyword or semantic query"),
    job_id: int | None = None,
    min_score: float | None = None,
    experience_min: float | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    # scope to the recruiter's own jobs
    job_ids = [j.id for j in JobRepository.list_for_owner(db, user.id)]
    if job_id and job_id not in job_ids:
        return {"query": q, "results": [], "mode": "keyword"}
    if job_id:
        job_ids = [job_id]

    rows: list[dict] = []
    for jid in job_ids:
        for cand in CandidateRepository.list_for_job(db, jid):
            res = ScreeningRepository.get_for_candidate(db, jid, cand.id)
            score = res.final_score if res else None
            if min_score is not None and (score is None or score < min_score):
                continue
            if experience_min is not None and cand.total_experience_years < experience_min:
                continue
            rows.append({
                "candidate_id": cand.id, "job_id": jid, "name": cand.name,
                "status": cand.status, "final_score": score,
                "rank": res.rank if res else None,
                "eligibility_status": res.eligibility_status if res else None,
                "missing_requirements": (res.missing_requirements if res else []) or [],
                "total_experience_years": cand.total_experience_years,
                "blob": _candidate_blob(cand),
            })

    mode = "keyword"
    if q:
        from app.services.embedding_service.embedder import get_embedder

        embedder = get_embedder()
        try:
            vecs = embedder.encode([q] + [r["blob"][:4000] for r in rows]) if rows else None
            mode = "semantic"
        except Exception:
            vecs = None
            mode = "keyword"
        if vecs is not None:
            qv = vecs[0]
            for i, r in enumerate(rows, start=1):
                r["semantic_score"] = round(max(0.0, embedder.similarity(qv, vecs[i])) * 100, 1)
            rows.sort(key=lambda r: r.get("semantic_score", 0), reverse=True)
        else:
            needle = q.lower()
            rows = [r for r in rows if needle in r["blob"].lower()]
    else:
        rows.sort(key=lambda r: (r["final_score"] is None, -(r["final_score"] or 0)))

    for r in rows:
        r.pop("blob", None)
    return {"query": q, "mode": mode, "results": rows[:100]}
