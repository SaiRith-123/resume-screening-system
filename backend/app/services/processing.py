"""Resume ingestion + analysis service (spec §4, §5, §11, §21).

Turns an uploaded resume into a structured Candidate (sub-entities persisted),
then transitions the candidate through its processing states.
"""
from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.candidate import Candidate, Certification, Education, Experience, Project, Resume
from app.models.skill import CandidateSkill, Skill
from app.schemas.resume import ResumeSchema
from app.services.resume_parser.extractor import extract
from app.utils.files import read_stored_file
from app.services.resume_parser.resume_structurer import deterministic_structure
from app.services.scoring_engine.experience import experience_intervals, total_experience_years
from app.services.screening.pipeline import build_candidate_skill_map
from app.workers.states import CandidateStatus

logger = get_logger(__name__)


def _parse_date(value):
    from app.services.scoring_engine.experience import _to_date

    return _to_date(value)


def ingest_resume(db: Session, candidate: Candidate, resume: Resume, use_llm: bool = False) -> Candidate:
    """Extract text + structure a single resume and persist structured data."""
    candidate.status = CandidateStatus.PROCESSING.value
    db.flush()

    extraction_path = resume.stored_path
    temporary_path = None
    if extraction_path.startswith("s3://"):
        import tempfile

        suffix = ".pdf" if resume.content_type == "application/pdf" else ".docx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(read_stored_file(extraction_path))
            temporary_path = handle.name
        extraction_path = temporary_path
    result = extract(extraction_path, resume.content_type)
    if temporary_path:
        import os

        os.unlink(temporary_path)
    resume.page_count = result.page_count
    resume.extraction_method = result.method
    if not result.ok:
        candidate.status = CandidateStatus.FAILED.value
        candidate.processing_error = result.error or "extraction_failed"
        db.commit()
        return candidate
    resume.extracted_text = result.text
    candidate.status = CandidateStatus.EXTRACTED.value

    llm = None
    if use_llm:
        try:
            from app.services.llm_service.providers import get_llm_provider

            llm = get_llm_provider()
            if getattr(llm, "name", "") == "null":
                llm = None
        except Exception:
            llm = None

    structured = deterministic_structure(result.text)
    if llm is not None:
        try:
            from app.services.resume_parser.resume_structurer import _llm_merge

            structured = _llm_merge(structured, result.text, llm)
        except Exception as exc:  # pragma: no cover
            logger.warning("LLM merge skipped: %s", exc)

    _persist_structured(db, candidate, structured)
    candidate.status = CandidateStatus.ANALYZED.value
    candidate.processing_error = None
    db.commit()
    db.refresh(candidate)
    return candidate


def _persist_structured(db: Session, candidate: Candidate, structured: ResumeSchema) -> None:
    candidate.name = structured.candidate_name or candidate.name
    candidate.email = structured.contact.email or candidate.email
    candidate.phone = structured.contact.phone or candidate.phone
    candidate.summary = structured.summary or candidate.summary
    candidate.structured = structured.model_dump()
    candidate.total_experience_years = total_experience_years(
        [e.model_dump() for e in structured.experience]
    )

    # reset derived rows (idempotent re-processing)
    for model in (CandidateSkill, Experience, Education, Project, Certification):
        db.execute(delete(model).where(model.candidate_id == candidate.id))

    skill_map = build_candidate_skill_map(candidate.structured)
    for canon, meta in skill_map.items():
        from app.services.skill_matcher.taxonomy import category_of

        skill_row = _ensure_skill(db, canon, category_of(canon))
        db.add(CandidateSkill(
            candidate_id=candidate.id,
            skill_id=skill_row.id if skill_row else None,
            raw_name=canon,
            normalized_name=canon,
            category=category_of(canon),
            evidence_context=meta.get("context", "list"),
            evidence_strength=meta.get("strength", 0.5),
        ))

    for exp in structured.experience:
        iv = experience_intervals([exp.model_dump()])
        months = 0.0
        if iv:
            s, e = iv[0]
            months = max(0.0, (e.year - s.year) * 12 + (e.month - s.month))
        db.add(Experience(
            candidate_id=candidate.id,
            company=exp.company, title=exp.title, description=exp.description,
            start_date=_parse_date(exp.start_date), end_date=_parse_date(exp.end_date),
            is_current=exp.is_current, kind=exp.kind, duration_months=round(months, 1),
        ))
    for edu in structured.education:
        db.add(Education(
            candidate_id=candidate.id, degree=edu.degree, field_of_study=edu.field_of_study,
            institution=edu.institution, start_year=edu.start_year, end_year=edu.end_year,
            grade=edu.grade,
        ))
    for proj in structured.projects:
        db.add(Project(
            candidate_id=candidate.id, name=proj.name, description=proj.description,
            technologies=proj.technologies,
        ))
    for cert in structured.certifications:
        db.add(Certification(
            candidate_id=candidate.id, name=cert.name, issuer=cert.issuer, year=cert.year,
        ))
    db.flush()


def _ensure_skill(db: Session, canonical: str, category: str) -> Skill | None:
    from sqlalchemy import select

    row = db.scalar(select(Skill).where(Skill.canonical_name == canonical))
    if row is None:
        row = Skill(canonical_name=canonical, category=category, aliases="")
        db.add(row)
        db.flush()
    return row


def reprocess_candidate(db: Session, candidate: Candidate) -> Candidate:
    resumes = list(candidate.resumes)
    if not resumes:
        candidate.status = CandidateStatus.FAILED.value
        candidate.processing_error = "no_resume"
        db.commit()
        return candidate
    return ingest_resume(db, candidate, resumes[0])
