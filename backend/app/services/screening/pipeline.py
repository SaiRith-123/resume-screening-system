"""End-to-end screening pipeline (spec §3, §8, §10, §13, §21).

Resume -> structured extraction -> NLP normalization -> requirement matching ->
embedding similarity -> deterministic scoring -> ranking -> LLM explanation.

The LLM only *explains*; it never computes the score (spec §33).
"""
from __future__ import annotations

import re

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.candidate import Candidate
from app.models.job import Job, JobRequirement
from app.models.screening import Embedding, ScreeningEvidence, ScreeningResult
from app.services.scoring_engine.education import match_education
from app.services.scoring_engine.experience import total_experience_years
from app.services.scoring_engine.scorer import component_scores, final_score
from app.services.screening.evidence import find_evidence
from app.services.screening.ranking import Rankable, eligibility_status, rank_candidates, recommendation
from app.services.skill_matcher.matcher import CONTEXT_STRENGTH, Matcher
from app.workers.states import CandidateStatus

logger = get_logger(__name__)

# Contexts in priority order for resolving a skill's strongest evidence (spec §8D)
_CONTEXT_ORDER = ["experience", "project", "certification", "summary", "skills", "list"]


def _model_dump(obj):
    return obj.model_dump() if hasattr(obj, "model_dump") else dict(obj)


def build_candidate_skill_map(structured: dict) -> dict[str, dict]:
    """Map normalized skill -> {context, evidence, strength} using strongest context."""
    structured = structured or {}
    name = structured.get("candidate_name")
    out: dict[str, dict] = {}

    def add(skill: str, context: str, evidence: str | None):
        from app.services.skill_matcher.normalizer import normalize_skill

        canon = normalize_skill(skill)
        if not canon:
            return
        strength = CONTEXT_STRENGTH.get(context, 0.5)
        prev = out.get(canon)
        if prev is None or strength > prev.get("strength", 0):
            out[canon] = {"context": context, "evidence": evidence, "strength": strength}

    # skills lists (context: skills)
    for key in ("skills", "technical_skills", "programming_languages", "frameworks",
                "databases", "cloud_technologies", "tools", "soft_skills"):
        for s in structured.get(key) or []:
            add(s, "skills", None)
    if structured.get("summary"):
        add_from_text(structured["summary"], "summary", add)
    for exp in structured.get("experience") or []:
        add_from_text(_exp_text(exp), "experience", add)
    for proj in structured.get("projects") or []:
        add_from_text(_proj_text(proj), "project", add)
        for t in proj.get("technologies") or []:
            add(t, "project", _proj_text(proj)[:240])
    for cert in structured.get("certifications") or []:
        add_from_text(str(cert.get("name") or ""), "certification", add)
    _ = name
    return out


def add_from_text(text: str, context: str, add) -> None:
    """Detect taxonomy skills inside free text and register with context."""
    from app.services.skill_matcher.taxonomy import ALIAS_TO_CANONICAL

    low = (text or "").lower()
    for alias, canon in ALIAS_TO_CANONICAL.items():
        if re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", low):
            sent = find_evidence(canon, text, context) or text.strip()[:240]
            add(canon, context, sent)


def _exp_text(exp: dict) -> str:
    return " ".join(str(exp.get(k, "")) for k in ("title", "company", "description"))


def _proj_text(proj: dict) -> str:
    return " ".join(str(proj.get(k, "")) for k in ("name", "description"))


def _candidate_corpus(structured: dict) -> str:
    parts = [structured.get("summary") or ""]
    for exp in structured.get("experience") or []:
        parts.append(_exp_text(exp))
    for proj in structured.get("projects") or []:
        parts.append(_proj_text(proj))
    parts.append(" ".join(structured.get("skills") or []))
    return "\n".join(p for p in parts if p)


def _job_corpus(job: Job) -> str:
    reqs = " ".join(r.value for r in job.requirements) if getattr(job, "requirements", None) else ""
    return f"{job.title}\n{job.description}\n{reqs}"


def _semantic_similarity(candidate_text: str, job_text: str, embedder) -> float:
    if not candidate_text.strip() or not job_text.strip():
        return 0.0
    try:
        from app.services.nlp_features import tfidf_cosine_similarity

        lexical = tfidf_cosine_similarity(candidate_text, job_text)
        vecs = embedder.encode([candidate_text[:4000], job_text[:4000]])
        embedding = max(0.0, embedder.similarity(vecs[0], vecs[1]))
        # Lexical overlap remains useful for named technologies; embeddings capture
        # paraphrases. Keep both signals in the explainable semantic component.
        return round((0.45 * lexical) + (0.55 * embedding), 6)
    except Exception as exc:  # pragma: no cover
        logger.warning("Embedding failed, semantic=0: %s", exc)
        return 0.0


def _project_relevance(structured: dict, job: Job, embedder) -> float:
    projects = structured.get("projects") or []
    if not projects:
        return 0.0
    job_text = _job_corpus(job)
    texts = [_proj_text(p) for p in projects][:5]
    try:
        vecs = embedder.encode([job_text[:2000]] + [t[:1500] for t in texts])
        sims = [embedder.similarity(vecs[0], v) for v in vecs[1:]]
        return max(0.0, sum(sims) / max(1, len(sims)))
    except Exception:
        # fallback: token overlap with required skills
        req = {r.value.lower() for r in job.requirements if r.priority == "required"}
        joined = " ".join(texts).lower()
        hits = sum(1 for r in req if r in joined)
        return hits / max(1, len(req))


def _requirements_of_kind(job: Job, kind: str, priority: str) -> list[str]:
    return [r.value for r in job.requirements if r.kind == kind and r.priority == priority]


def screen_candidate(db: Session, job: Job, candidate: Candidate, embedder=None,
                     matcher: Matcher | None = None, persist: bool = True) -> ScreeningResult:
    """Compute (and optionally persist) the full screening result for one candidate."""
    if embedder is None:
        from app.services.embedding_service.embedder import get_embedder

        embedder = get_embedder()
    if matcher is None:
        matcher = Matcher(embedder)

    structured = candidate.structured or {}
    skill_map = build_candidate_skill_map(structured)
    candidate_years = candidate.total_experience_years or total_experience_years(
        structured.get("experience") or []
    )

    required_skills = _requirements_of_kind(job, "skill", "required") + _requirements_of_kind(
        job, "technology", "required"
    )
    preferred_skills = _requirements_of_kind(job, "skill", "preferred") + _requirements_of_kind(
        job, "technology", "preferred"
    )
    required_certs = _requirements_of_kind(job, "certification", "required")
    required_edu = _requirements_of_kind(job, "education", "required")
    exp_reqs = [r for r in job.requirements if r.kind == "experience"]
    min_years = min((r.min_years for r in exp_reqs if r.min_years), default=None)

    required_matches = matcher.match_many(skill_map, required_skills)
    preferred_matches = matcher.match_many(skill_map, preferred_skills)

    sim = _semantic_similarity(_candidate_corpus(structured), _job_corpus(job), embedder)
    proj_rel = _project_relevance(structured, job, embedder)

    components = component_scores(
        required_matches=required_matches,
        preferred_matches=preferred_matches,
        candidate_years=candidate_years,
        min_years=min_years,
        semantic_similarity=sim,
        candidate_education=structured.get("education") or [],
        required_education=required_edu,
        candidate_certifications=structured.get("certifications") or [],
        required_certifications=required_certs,
        project_relevance=proj_rel,
        n_projects=len(structured.get("projects") or []),
    )
    weights = job.weights or {}
    score = final_score(components, weights)

    # Evidence + missing/partial/matched skill lists (spec §9, §13)
    missing_required: list[str] = []
    missing_hard: list[str] = []
    hard_values = {r.value for r in job.requirements if r.is_hard_gate}
    matched, partial, missing = [], [], []
    evidence_rows: list[ScreeningEvidence] = []
    resume_text = _resume_text(candidate)
    for m in required_matches:
        ev = m.evidence or find_evidence(m.skill, resume_text)
        if m.status == "MATCH":
            matched.append(m.skill)
        elif m.status == "PARTIAL_MATCH":
            partial.append(m.skill)
            missing_required.append(m.skill)
        else:
            missing.append(m.skill)
            missing_required.append(m.skill)
        if m.skill in hard_values and m.status != "MATCH":
            missing_hard.append(m.skill)
        evidence_rows.append(ScreeningEvidence(
            requirement=m.skill,
            requirement_kind="skill",
            status=m.status,
            confidence=m.confidence,
            evidence_text=ev,
            source="resume",
        ))

    # Eligibility is broader than skill matching. Required experience,
    # education, and certification requirements must contribute the same
    # missing/hard-gate signals as required skills.
    for requirement in exp_reqs:
        minimum = requirement.min_years
        matched_exp = minimum is None or candidate_years >= minimum
        status = "MATCH" if matched_exp else "MISSING"
        if not matched_exp:
            missing_required.append(requirement.value)
            if requirement.is_hard_gate:
                missing_hard.append(requirement.value)
        evidence_rows.append(ScreeningEvidence(
            requirement=requirement.value,
            requirement_kind="experience",
            status=status,
            confidence=1.0 if matched_exp else 0.0,
            evidence_text=f"{candidate_years:.1f} years experience",
            source="resume",
        ))

    if required_edu:
        edu_status, _ = match_education(structured.get("education") or [], required_edu)
        for requirement in required_edu:
            matched_edu = edu_status == "MATCH"
            if not matched_edu:
                missing_required.append(requirement)
            row = next((r for r in job.requirements
                        if r.kind == "education" and r.priority == "required"
                        and r.value == requirement), None)
            if not matched_edu and row and row.is_hard_gate:
                missing_hard.append(requirement)
            evidence_rows.append(ScreeningEvidence(
                requirement=requirement,
                requirement_kind="education",
                status=edu_status,
                confidence=1.0 if edu_status == "MATCH" else 0.0,
                evidence_text="; ".join(
                    str(item.get("degree") or item.get("field_of_study") or "")
                    for item in structured.get("education") or []
                )[:240] or None,
                source="resume",
            ))

    certifications = structured.get("certifications") or []
    cert_blob = " ".join(
        f"{item.get('name', '')} {item.get('issuer', '')}" for item in certifications
    ).lower()
    for requirement in required_certs:
        matched_cert = requirement.lower() in cert_blob
        status = "MATCH" if matched_cert else "MISSING"
        if not matched_cert:
            missing_required.append(requirement)
            row = next((r for r in job.requirements
                        if r.kind == "certification" and r.priority == "required"
                        and r.value == requirement), None)
            if row and row.is_hard_gate:
                missing_hard.append(requirement)
        evidence_rows.append(ScreeningEvidence(
            requirement=requirement,
            requirement_kind="certification",
            status=status,
            confidence=1.0 if matched_cert else 0.0,
            evidence_text=cert_blob[:240] or None,
            source="resume",
        ))

    elig = eligibility_status(missing_hard, missing_required, bool(job.hard_gate))
    needs_review = elig != "MEETS_ALL_MANDATORY" or score < 70
    rec = recommendation(score, elig, needs_review)

    if persist:
        result = ScreeningResult(
            job_id=job.id,
            candidate_id=candidate.id,
            skill_score=components["skill"],
            experience_score=components["experience"],
            semantic_score=components["semantic"],
            education_score=components["education"],
            project_score=components["project"],
            certification_score=components["certification"],
            preferred_score=components["preferred"],
            final_score=score,
            weights=weights,
            eligibility_status=elig,
            missing_requirements=sorted(set(missing_required)),
            matched_skills=matched,
            partial_skills=partial,
            missing_skills=missing,
            recommendation=rec,
            needs_review=needs_review,
        )
        result.evidence = evidence_rows
        return result
    # non-persisting path returns an in-memory, unsaved object for previewing
    result = ScreeningResult(
        job_id=job.id, candidate_id=candidate.id,
        skill_score=components["skill"], experience_score=components["experience"],
        semantic_score=components["semantic"], education_score=components["education"],
        project_score=components["project"], certification_score=components["certification"],
        preferred_score=components["preferred"], final_score=score, weights=weights,
        eligibility_status=elig, missing_requirements=sorted(set(missing_required)),
        matched_skills=matched, partial_skills=partial, missing_skills=missing,
        recommendation=rec, needs_review=needs_review,
    )
    result.evidence = evidence_rows
    return result


def _resume_text(candidate: Candidate) -> str:
    for r in getattr(candidate, "resumes", []) or []:
        if r.extracted_text:
            return r.extracted_text
    return candidate.summary or ""


def run_screening(db: Session, job_id: int, candidate_ids: list[int] | None = None,
                  weights: dict | None = None, embedder=None) -> list[ScreeningResult]:
    """Screen all (or a subset of) candidates for a job and persist results, then rank."""
    job = db.get(Job, job_id)
    if job is None:
        raise ValueError(f"job {job_id} not found")
    if weights:
        job.weights = weights

    stmt = select(Candidate).where(Candidate.job_id == job_id)
    if candidate_ids:
        stmt = stmt.where(Candidate.id.in_(candidate_ids))
    candidates = list(db.scalars(stmt).all())

    # clear previous results for these candidates to keep history idempotent
    ids = [c.id for c in candidates]
    if ids:
        db.execute(delete(ScreeningResult).where(
            ScreeningResult.job_id == job_id, ScreeningResult.candidate_id.in_(ids)
        ))
        db.flush()

    if embedder is None:
        from app.services.embedding_service.embedder import get_embedder

        embedder = get_embedder()
    matcher = Matcher(embedder)

    results: list[ScreeningResult] = []
    for cand in candidates:
        if cand.status == CandidateStatus.FAILED.value:
            continue
        try:
            res = screen_candidate(db, job, cand, embedder=embedder, matcher=matcher, persist=True)
            db.add(res)
            db.flush()
            cand.status = CandidateStatus.SCREENED.value
            results.append(res)
        except Exception as exc:  # one bad candidate must not break the batch (spec §23)
            logger.exception("Screening failed for candidate %s: %s", cand.id, exc)
            cand.status = CandidateStatus.FAILED.value
            cand.processing_error = f"screening_failed: {exc}"
    db.flush()

    # rank (spec §10, §17)
    rankables = [
        Rankable(r.candidate_id, r.final_score, r.eligibility_status, r.missing_requirements or [])
        for r in results
    ]
    ordered = rank_candidates(rankables)
    for rank, item in enumerate(ordered, start=1):
        db.execute(update(ScreeningResult)
                   .where(ScreeningResult.job_id == job_id,
                          ScreeningResult.candidate_id == item.candidate_id)
                   .values(rank=rank))
    db.commit()
    for r in results:
        db.refresh(r)
    return results


def store_embedding(db: Session, owner_type: str, owner_id: int, vector, field: str = "text",
                    model_name: str | None = None) -> Embedding:
    from app.core.config import settings

    emb = Embedding(
        owner_type=owner_type, owner_id=owner_id, field=field,
        model_name=model_name or settings.EMBEDDING_MODEL,
        dim=len(list(vector)), vector=list(vector),
    )
    db.add(emb)
    return emb


def get_education_status(candidate: Candidate, job: Job) -> tuple[str, float]:
    req = _requirements_of_kind(job, "education", "required")
    return match_education((candidate.structured or {}).get("education") or [], req)
