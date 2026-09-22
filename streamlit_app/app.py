"""Intelligent Resume Screening - Streamlit web app.

A complete, self-contained website: create a job, upload PDF/DOCX resumes,
screen/rank candidates, inspect explainable scores + evidence, and export CSV.

Runs on SQLite with the deterministic hashing embedder by default, so it works
on Streamlit Community Cloud with zero infrastructure. See DEPLOY.md.
"""
from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

DATA_DIR = APP_DIR / "data"
(DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'rss.db').as_posix()}")
os.environ.setdefault("UPLOAD_DIR", str(DATA_DIR / "uploads"))
os.environ.setdefault("USE_CELERY", "false")
# Set EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 (and install
# sentence-transformers) for true semantic embeddings; without it a
# deterministic hashing embedder is used.
os.environ.setdefault("EMBEDDING_MODEL", "none")
# Set LLM_PROVIDER=openai (plus OPENAI_API_KEY) to enable GenAI explanations.
os.environ.setdefault("LLM_PROVIDER", "null")

import streamlit as st  # noqa: E402
import pandas as pd  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.db.init_db import init_db  # noqa: E402
from app.db.session import new_session  # noqa: E402
from app.models.job import Job  # noqa: E402
from app.repositories.candidate_repo import CandidateRepository  # noqa: E402
from app.repositories.job_repo import JobRepository  # noqa: E402
from app.repositories.screening_repo import ScreeningRepository  # noqa: E402
from app.services.processing import ingest_resume  # noqa: E402
from app.services.screening.pipeline import run_screening  # noqa: E402
from app.utils.files import FileValidationError, store_upload  # noqa: E402

init_db()

DISCLAIMER = (
    "This system provides decision-support recommendations. Final hiring decisions "
    "should be made by qualified human reviewers."
)


# ----------------------------------------------------------- data layer ----
def list_jobs() -> list[Job]:
    db = new_session()
    try:
        return list(db.scalars(select(Job).order_by(Job.created_at.desc())).all())
    finally:
        db.close()


def load_demo_data():
    from app.db.seed import seed

    return seed()


def create_job(title: str, description: str, required: list[str], preferred: list[str],
               min_years: float | None, hard_gate: bool) -> int:
    reqs = [{"kind": "skill", "priority": "required", "value": s} for s in required]
    reqs += [{"kind": "skill", "priority": "preferred", "value": s} for s in preferred]
    if min_years and min_years > 0:
        reqs.append({"kind": "experience", "priority": "required", "value": "minimum experience",
                     "min_years": min_years})
    db = new_session()
    try:
        job = JobRepository.create(db, 1, {"title": title, "description": description,
                                           "weights": {}, "hard_gate": hard_gate}, reqs)
        return job.id
    finally:
        db.close()


def upload_and_screen(job_id: int, files):
    accepted, rejected = [], []
    db = new_session()
    try:
        for f in files:
            content = f.getvalue()
            try:
                v = store_upload(f.name, content, f.type, job_id)
            except FileValidationError as exc:
                rejected.append({"filename": f.name, "reason": str(exc)})
                continue
            if CandidateRepository.find_duplicate(db, job_id, v.sha256):
                rejected.append({"filename": f.name, "reason": "duplicate_resume"})
                continue
            cand = CandidateRepository.create(db, job_id)
            CandidateRepository.add_resume(
                db, cand.id, original_filename=v.safe_name, stored_path=v.stored_path,
                content_type=v.content_type, size_bytes=v.size_bytes, sha256=v.sha256,
            )
            try:
                ingest_resume(db, cand, cand.resumes[0])
                accepted.append({"filename": v.safe_name, "name": cand.name, "id": cand.id})
            except Exception as exc:  # noqa: BLE001
                cand.processing_error = str(exc)
                rejected.append({"filename": f.name, "reason": f"processing_error: {exc}"})
        run_screening(db, job_id)
    finally:
        db.close()
    return accepted, rejected


def rescreen(job_id: int) -> None:
    db = new_session()
    try:
        run_screening(db, job_id)
    finally:
        db.close()


def get_results(job_id: int):
    db = new_session()
    try:
        candidates = {c.id: c for c in CandidateRepository.list_for_job(db, job_id)}
        results = ScreeningRepository.list_for_job(db, job_id)
        rows = []
        for r in results:
            cand = candidates.get(r.candidate_id)
            rows.append({
                "rank": r.rank,
                "candidate": (cand.name if cand and cand.name else f"Candidate {r.candidate_id}"),
                "candidate_id": r.candidate_id,
                "final_score": round(r.final_score, 1),
                "eligibility": r.eligibility_status,
                "skill": round(r.skill_score, 1),
                "experience": round(r.experience_score, 1),
                "semantic": round(r.semantic_score, 1),
                "education": round(r.education_score, 1),
                "missing": ", ".join(r.missing_skills or []) or "-",
                "status": cand.status if cand else "?",
            })
        return results, candidates, rows
    finally:
        db.close()


def csv_for_job(job_id: int) -> bytes:
    results, candidates, _ = get_results(job_id)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Candidate", "Overall Score", "Eligibility", "Matched Skills",
                     "Missing Skills", "Experience", "Recommendation"])
    for r in results:
        cand = candidates.get(r.candidate_id)
        writer.writerow([
            (cand.name if cand and cand.name else f"Candidate {r.candidate_id}"),
            f"{r.final_score:.1f}%",
            r.eligibility_status,
            ", ".join(r.matched_skills or []),
            ", ".join(r.missing_skills or []),
            f"{cand.total_experience_years if cand else 0:.1f} yrs",
            r.recommendation,
        ])
    return buf.getvalue().encode("utf-8")


# ------------------------------------------------------------------ UI ----
def main() -> None:
    st.set_page_config(
        page_title="Intelligent Resume Screening",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🎯 Intelligent Resume Screening")
    st.caption(DISCLAIMER)

    if "job_id" not in st.session_state:
        st.session_state.job_id = None

    with st.sidebar:
        st.header("1 · Job")
        jobs = list_jobs()
        job_titles = ["＋ Create a new job"] + [f"{j.id} · {j.title}" for j in jobs]
        current = st.session_state.job_id
        default_index = 0
        if current:
            for i, label in enumerate(job_titles):
                if label.startswith(f"{current} ·"):
                    default_index = i
                    break
        choice = st.selectbox("Active job", job_titles, index=default_index)

        if choice == "＋ Create a new job":
            with st.form("job_form", clear_on_submit=False):
                title = st.text_input("Job title", "Machine Learning Engineer")
                description = st.text_area(
                    "Job description",
                    "Develop machine learning models and build production ML pipelines.",
                    height=140)
                required = st.text_input("Mandatory skills (comma-separated)",
                                         "Python, SQL, Machine Learning")
                preferred = st.text_input("Preferred skills (comma-separated)",
                                          "PyTorch, AWS, Docker")
                min_years = st.number_input("Minimum years of experience", 0.0, 20.0, 2.0, 0.5)
                hard_gate = st.checkbox("Treat missing mandatory requirements as a hard gate",
                                        value=False)
                submitted = st.form_submit_button("Create job", width="stretch")
            if submitted and title.strip():
                req = [s.strip() for s in required.split(",") if s.strip()]
                pref = [s.strip() for s in preferred.split(",") if s.strip()]
                st.session_state.job_id = create_job(title.strip(), description.strip(),
                                                     req, pref, float(min_years), hard_gate)
                st.rerun()
        else:
            st.session_state.job_id = int(choice.split(" · ")[0])

        st.header("Demo data")
        if st.button("Load 5 demo jobs + 10 resumes", width="stretch"):
            with st.spinner("Seeding demo data…"):
                load_demo_data()
            if st.session_state.job_id is None:
                st.session_state.job_id = list_jobs()[0].id
            st.rerun()

    job_id = st.session_state.job_id
    if job_id is None:
        st.info("Create a job in the sidebar (or load the demo data) to begin.")
        return

    db = new_session()
    try:
        job = db.get(Job, job_id)
    finally:
        db.close()
    if job is None:
        st.error("The selected job no longer exists (the database may have been reset). "
                 "Pick another job or create a new one.")
        st.session_state.job_id = None
        return

    st.subheader(f"2 · Upload resumes for “{job.title}”")
    files = st.file_uploader("Resumes (PDF or DOCX)", type=["pdf", "docx"],
                             accept_multiple_files=True)
    col_a, col_b, _ = st.columns([1, 1, 3])
    with col_a:
        run_clicked = st.button("Upload & screen", type="primary",
                                disabled=not files, width="stretch")
    with col_b:
        rescreen_clicked = st.button("Re-run screening", width="stretch")

    if run_clicked and files:
        with st.spinner("Extracting, matching and scoring…"):
            accepted, rejected = upload_and_screen(job_id, files)
        if accepted:
            st.success(f"Processed {len(accepted)} resume(s): " +
                       ", ".join(a["name"] or a["filename"] for a in accepted))
        for r in rejected:
            st.warning(f"{r['filename']}: {r['reason']}")
        st.rerun()

    if rescreen_clicked:
        with st.spinner("Re-running screening…"):
            rescreen(job_id)
        st.rerun()

    results, candidates, rows = get_results(job_id)

    st.subheader("3 · Ranking")
    if not rows:
        st.info("No screening results yet. Upload resumes above, or load the demo data.")
        return

    df = pd.DataFrame(rows)
    st.dataframe(
        df[["rank", "candidate", "final_score", "eligibility", "skill", "experience",
            "semantic", "education", "missing", "status"]],
        width="stretch",
        hide_index=True,
        height=320,
    )

    avg = sum(r["final_score"] for r in rows) / len(rows)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Candidates", len(rows))
    m2.metric("Average match", f"{avg:.1f}%")
    m3.metric("Meets all mandatory",
              sum(1 for r in rows if r["eligibility"] == "MEETS_ALL_MANDATORY"))
    m4.metric("Needs review",
              sum(1 for r in rows if r["eligibility"] != "MEETS_ALL_MANDATORY"))

    st.subheader("4 · Candidate detail")
    labels = {r["candidate_id"]: f"#{r['rank']} {r['candidate']} — {r['final_score']}"
              for r in rows}
    sel_id = st.selectbox("Candidate", list(labels.keys()), format_func=lambda k: labels[k])
    result = next((r for r in results if r.candidate_id == sel_id), None)
    cand = candidates.get(sel_id)

    if not (result and cand):
        st.warning("No screening result for this candidate yet.")
        return

    structured = cand.structured or {}
    scores = {
        "Skill": result.skill_score, "Experience": result.experience_score,
        "Semantic": result.semantic_score, "Education": result.education_score,
        "Projects": result.project_score, "Certifications": result.certification_score,
        "Preferred": result.preferred_score,
    }
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Final score", f"{result.final_score:.1f}%")
        st.caption(f"Eligibility: {result.eligibility_status}")
        if result.missing_requirements:
            st.warning("Missing: " + ", ".join(result.missing_requirements))
        else:
            st.success("Meets all mandatory requirements")
        st.bar_chart(pd.DataFrame({"score": scores}))
    with c2:
        st.markdown("**Skills (matched / partial / missing)**")
        st.markdown(
            "· Matched: " + (", ".join(result.matched_skills or []) or "—") + "  \n"
            "· Partial: " + (", ".join(result.partial_skills or []) or "—") + "  \n"
            "· Missing: " + (", ".join(result.missing_skills or []) or "—")
        )
        st.markdown("**Evidence (verbatim from the resume)**")
        for e in result.evidence:
            icon = "✅" if e.status == "MATCH" else ("🟡" if e.status == "PARTIAL_MATCH" else "❌")
            with st.expander(f"{icon} {e.requirement} — {e.status} ({e.confidence:.0%})"):
                st.write(e.evidence_text or "_No evidence found in resume._")
        st.caption(DISCLAIMER)

    with st.expander("Profile: experience, education, projects, certifications"):
        st.markdown(f"**Summary:** {structured.get('summary') or '—'}")
        st.markdown("**Experience**")
        for e in structured.get("experience") or []:
            dates = (f"{e.get('start_date') or '?'} – "
                     f"{'Present' if e.get('is_current') else e.get('end_date') or '?'}")
            st.markdown(f"- **{e.get('title') or 'Role'}** · {e.get('company') or ''} · "
                        f"{dates} · {e.get('kind')}")
            if e.get("description"):
                st.markdown(f"  > {e['description'][:280]}")
        st.markdown("**Education**")
        for e in structured.get("education") or []:
            parts = [v for v in (e.get("degree"), e.get("field_of_study"),
                                 e.get("institution")) if v]
            st.markdown(f"- {', '.join(parts)}")
        st.markdown("**Projects**")
        for p in structured.get("projects") or []:
            st.markdown(f"- **{p.get('name') or 'Project'}** — {(p.get('description') or '')[:200]}")
        st.markdown("**Certifications**")
        for c in structured.get("certifications") or []:
            st.markdown(f"- {c.get('name') or '—'}")

    st.download_button("Download screening report (CSV)",
                       data=csv_for_job(job_id),
                       file_name=f"{job.title.replace(' ', '_').lower()}_screening.csv",
                       mime="text/csv", width="stretch")


if os.environ.get("RSS_BARE_IMPORT") != "1":
    main()
