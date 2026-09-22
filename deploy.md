# DEPLOYMENT GUIDE — Streamlit Demo

> This guide deploys the separate Streamlit demo. For the Firebase-enabled
> production website, use the React + FastAPI deployment described in
> `readme.md` and `docker-compose.yml`.

The project ships with a complete Streamlit website
(`streamlit_app/app.py`) that contains the entire product: create a job,
upload PDF/DOCX resumes, screen and rank candidates with explainable scores,
inspect verbatim evidence, and export a CSV report. It runs on SQLite and
needs **no database service, no Docker, and no secrets**.

---

## 1. Run locally

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. The app creates its SQLite database and upload
folder automatically under `streamlit_app/data/`.

Fastest way to see it working: click **Load 5 demo jobs + 10 resumes** in the
sidebar, then pick a job and browse the ranking.

---

## 2. Deploy to Streamlit Community Cloud (free)

1. Push this repository to GitHub (public or private).
2. Go to <https://share.streamlit.io> → **New app**.
3. Repository: your repo · Branch: `main`.
4. **Main file path:** `streamlit_app/app.py`
5. Click **Deploy**. The first build installs
   `streamlit_app/requirements.txt` (about 2–4 minutes).

That's the whole process. Nothing else to configure.

### Optional settings (Advanced settings → Secrets)

| Setting | Effect |
|---|---|
| `EMBEDDING_MODEL` = `sentence-transformers/all-MiniLM-L6-v2` and add `sentence-transformers` to `streamlit_app/requirements.txt` | True semantic embeddings (heavy — pulls in torch and may exceed the free tier's ~1 GB RAM) |
| `LLM_PROVIDER` = `openai` and `OPENAI_API_KEY` = your key | Enables GenAI summaries, explanations and interview questions |

Without these the app uses the deterministic hashing embedder and rule-based
interview questions — every other feature works identically.

---

## 3. How the app works

| Stage | What happens |
|---|---|
| Job setup | Title, description, mandatory skills, preferred skills, minimum years, optional hard gate → stored as structured requirements |
| Upload | PDF/DOCX validated (type, size, duplicates) and saved under `streamlit_app/data/uploads/` |
| Extraction | `pdfplumber` / `python-docx` pull the text; sections are detected; structured candidate data is built |
| Matching | Exact → fuzzy (RapidFuzz) → semantic (embeddings) → related (taxonomy partial credit), with context-aware evidence strength |
| Scoring | Seven components (skill 35%, experience 20%, semantic 15%, education 10%, projects 10%, certifications 5%, preferred 5%) combined into a final score |
| Ranking | Candidates sorted with eligibility gating — missing mandatory requirements are flagged, never silently rejected |
| Detail | Score chart, matched/partial/missing skills, verbatim evidence, profile, CSV download |

## 4. Customizing

| Change | File / location |
|---|---|
| Page title, theme, colors | `streamlit_app/.streamlit/config.toml` and the `st.title` line in `app.py` |
| Default job / requirements in the form | The `st.text_input` / `st.text_area` defaults in `main()` in `app.py` |
| Scoring weights | `st.number_input`/form section, or edit `app/services/scoring_engine/weights.py` |
| Skill taxonomy and aliases | `backend/app/services/skill_matcher/taxonomy.py` |
| Demo data | `sample_data/job_descriptions/` and `sample_data/resumes/` |
| Disclaimer text | `DISCLAIMER` constant at the top of `app.py` |

## 5. Limits to know about

- Data lives in `streamlit_app/data/rss.db` (SQLite). On Community Cloud it
  resets when the app reboots or redeploys — demo-grade storage.
- One malformed resume never breaks the batch: bad types, oversized files and
  duplicates are reported inline.
- The decision-support disclaimer is always visible, and protected attributes
  (age, gender, photo, religion, …) are never used in scoring.

The full FastAPI + PostgreSQL/pgvector stack ( recruiter accounts, API,
Celery workers) remains available via `docker compose up --build` when you
outgrow the single-user Streamlit deployment.
