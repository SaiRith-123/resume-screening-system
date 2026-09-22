# Intelligent Resume Screening & Candidate Ranking System

A production-quality, end-to-end web application that screens resumes against a
job description, extracts structured candidate information, computes
**explainable** compatibility scores, ranks candidates, and uses GenAI to produce
evidence-based summaries, screening explanations, and interview questions.

> **Decision-support, not autonomous hiring.** This system provides
> recommendations. Final hiring decisions should be made by qualified human reviewers.

---

## Table of contents
- [Features](#features)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Quick start (Docker)](#quick-start-docker)
- [Local development](#local-development)
- [Environment variables](#environment-variables)
- [Database setup](#database-setup)
- [API documentation](#api-documentation)
- [Example workflow](#example-workflow)
- [Model information](#model-information)
- [Scoring methodology](#scoring-methodology)
- [Testing](#testing)
- [Limitations](#limitations)
- [Fairness considerations](#fairness-considerations)
- [Security considerations](#security-considerations)
- [Deployment](#deployment)
- [Project layout](#project-layout)

---

## Features

- Create job postings with a full job description, **mandatory** and **preferred**
  requirements, and configurable hard eligibility gates.
- Upload multiple **PDF / DOCX** resumes (drag & drop) with validation, duplicate
  detection, safe filenames, and OCR fallback for scanned PDFs.
- Deterministic + NLP + optional LLM structured extraction into a validated schema.
- Multi-strategy matching: exact, fuzzy (RapidFuzz), taxonomy-related (partial
  credit), semantic (sentence-transformers embeddings), and context-aware evidence
  strength.
- Transparent, configurable **7-component scoring** — never a black box.
- Ranking with eligibility gating that **never silently rejects** a candidate.
- Evidence quoted verbatim from the resume; the LLM never fabricates experience.
- GenAI candidate summary, screening explanation, and interview-question generator
  with prompt-injection defenses.
- Recruiter dashboard, sortable/filterable/paginated ranking, candidate detail with
  charts, keyword + **semantic** search, and CSV/Excel/PDF export.
- Async, state-tracked resume processing that degrades gracefully on every failure.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md). The pipeline is:

```
Resume → File validation → PDF/DOCX extraction (+OCR) → Text cleaning
      → Section detection → Structured extraction → Skill normalization
      → Experience/education/project/certification extraction
      → JD parsing → Requirement classification → Multi-strategy matching
      → Embedding similarity → Deterministic scoring → Ranking
      → Evidence extraction → GenAI explanation → Recruiter dashboard
```

The LLM **enhances** the system; it does not compute the score (design principle §33).

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, React Router, Axios, Firebase Auth, Recharts, React Dropzone |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL + pgvector |
| NLP / ML | spaCy, sentence-transformers, scikit-learn, RapidFuzz, Hugging Face Transformers |
| GenAI | Provider abstraction (OpenAI / generic HTTP / local / null) |
| Infra | Docker, Docker Compose, environment variables |
| Async | Celery + Redis (with in-process fallback) |

## Quick start (Docker)

```bash
cp .env.example .env          # then edit secrets
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health

The backend container runs Alembic migrations, seeds sample data
(5 jobs + 10 resumes), and starts the API. A Celery worker container runs async jobs.

**Demo login** (created by the seed): `demo@recruiter.io` / `demo12345`
(override the password with the `DEMO_PASSWORD` environment variable).

## Included resume datasets

The curated demo resumes remain in `sample_data/resumes`. The imported Kaggle
corpus is in `sample_data/kaggle_resume_dataset/Resumes` and contains 228 DOCX
files for parser and screening evaluation. It has no reviewed labels, so it is
not used to claim supervised model training; see its README before using or
redistributing the files.

An auxiliary, weakly supervised role classifier can be reproduced with:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\train_resume_classifier.py
```

It uses role phrases inferred from filenames and resume text, records label
provenance in JSONL, and reports held-out metrics. It is not the hiring score:
the explainable deterministic matcher and scorer remain authoritative until
reviewed human labels are available.

## Local development

```bash
# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate      # Windows
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Deployment choice

Use the **React + FastAPI + PostgreSQL stack** for the Firebase-enabled website.
Firebase Auth is implemented in `frontend/` and the backend verifies Firebase
ID tokens with the Admin SDK. Build the frontend with the `VITE_*` Firebase
values and run the backend with the Admin SDK JSON mounted as a secret.

For a local Docker smoke test:

```powershell
Copy-Item .env.example .env
# Put the Firebase Admin JSON at the path in FIREBASE_SERVICE_ACCOUNT_FILE.
# Fill VITE_FIREBASE_API_KEY and change production secrets before deployment.
docker compose up --build
```

For production, deploy the backend and database on a service that supports
containers or Python (for example Render, Railway, Fly.io, or a managed VM),
and deploy the built frontend to a static host (for example Firebase Hosting,
Cloudflare Pages, or Vercel). Set `VITE_API_BASE_URL` to the public HTTPS API
URL, `CORS_ORIGINS` to the exact frontend origin, and add that frontend origin
to Firebase Authentication's authorized domains.

The `streamlit_app/` directory is a separate demo-grade SQLite application.
It is suitable for a quick Streamlit Community Cloud demonstration, but it is
not the Firebase-authenticated React website and does not use the FastAPI user
accounts or PostgreSQL data store.

## Environment variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing key (change in production) |
| `DATABASE_URL` | PostgreSQL + psycopg connection string |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `MAX_UPLOAD_MB` | Max resume size |
| `EMBEDDING_MODEL` / `EMBEDDING_DIM` | sentence-transformers model + vector size |
| `LLM_PROVIDER` | `openai` \| `generic` \| `local` \| `null` |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | OpenAI-compatible provider |
| `GENERIC_LLM_URL` / `GENERIC_LLM_API_KEY` | Any chat-completions endpoint |
| `LOCAL_LLM_URL` / `LOCAL_LLM_MODEL` | Ollama / vLLM |
| `USE_CELERY`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Async processing |

For OpenAI-enhanced resume extraction and explanations, set `LLM_PROVIDER=openai`
and `OPENAI_API_KEY` in your local `.env`. The key is read only by the backend
and is never sent to the frontend. Without a key, the deterministic parser,
matching, scoring, ranking, and fallback interview questions continue to work.

Secrets live only in environment variables. **No API keys are shipped to the frontend.**

### Optional Firebase sign-in

The web app supports official Google sign-in through Firebase Authentication.
This is optional: the existing email/password login works when Firebase is not
configured.

1. Create a Firebase project and add a Web App in the Firebase console.
2. Enable **Google** under Authentication → Sign-in method. Add the local and
  production frontend domains to the authorized domains list.
3. Copy the public Web App settings into the frontend `.env` using the
  `VITE_FIREBASE_*` variables from `frontend/.env.example`.
4. Configure the backend with `FIREBASE_PROJECT_ID` and Google Application
  Default Credentials, or set `GOOGLE_APPLICATION_CREDENTIALS` to a Firebase
  service-account JSON file. Never commit that file or put it in the frontend.

The browser exchanges the Firebase ID token for the app's normal short-lived
JWT. The backend verifies the token before creating or matching the local user
account. Terms of Service and Privacy Policy consent are required for the
Firebase sign-in path as well.

## Database setup

```bash
cd backend
alembic upgrade head          # create schema + pgvector extension
python -m app.db.seed         # optional demo data
```

Schema details: [DATABASE.md](DATABASE.md).

## API documentation

Full endpoint reference: [API.md](API.md). Interactive docs at `/docs`.

## Example workflow

1. Register / log in.
2. Create a job → paste the job description → add mandatory/preferred requirements.
3. Upload multiple PDF/DOCX resumes.
4. The system extracts, normalizes, matches, scores, ranks and explains each candidate.
5. Open the ranking table, then a candidate detail page to inspect the score
   breakdown, evidence, and AI explanation.
6. Generate interview questions; export CSV/Excel/PDF.

## Model information

- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim), normalized
  cosine similarity, cached on disk. The transformer model is required by
  default; the deterministic hashing encoder is available only as an explicit
  degraded backend for tests or offline diagnostics (`EMBEDDING_BACKEND=hash`).
- **spaCy:** `en_core_web_sm` for lightweight linguistic processing (optional).
- **RapidFuzz:** token-set ratio for fuzzy skill matching.
- **LLM:** provider-abstracted; the application is not coupled to one vendor.
- Details: [ML_PIPELINE.md](ML_PIPELINE.md).

## Scoring methodology

Default weights (configurable per job):

| Component | Weight |
|---|---|
| Skill Match | 35% |
| Experience Match | 20% |
| Semantic Relevance | 15% |
| Education Match | 10% |
| Project Relevance | 10% |
| Certification Match | 5% |
| Preferred Requirements | 5% |

`final_score = Σ (component × weight)`, each component normalized to 0–100.
Every component is stored separately. Full derivation is shown in the UI.

## Testing

```bash
cd backend
pytest            # 62 tests: unit + API + integration
```

### Screening-time benchmark

Run the reproducible benchmark against the 10 included sample profiles. It
cycles those profiles to test the real batch pipeline at 100 candidates and
compares wall-clock automation time with an explicit manual-review baseline:

```bash
cd backend
python scripts/benchmark_screening.py --candidates 100 --manual-minutes 5
```

The command exits successfully only when the configured reduction target (80%
by default) is met. The manual baseline must be replaced with an observed
recruiter average before making a production productivity claim.

Test groups: skill normalization, experience calculation, scoring, fuzzy
matching, semantic similarity, requirement classification, JD parsing,
prompt-injection guardrails, auth, job CRUD, upload validation, and the full
upload → extract → parse → match → score → rank integration path.

## Limitations

- OCR quality depends on the source scan; complex layouts/tables may extract imperfectly.
- Embedding quality depends on the chosen model; domain-specific resumes may need fine-tuning.
- Experience calculation relies on parseable dates; free-text dates reduce accuracy.
- The LLM explanation quality depends on the configured provider; without one, the
  system falls back to deterministic results with a clear notice.
- The system is decision **support** only and must be supervised by humans.

## Fairness considerations

- Scoring **excludes** gender, age/date of birth, race/ethnicity, religion,
  marital status, photograph, disability, home address, and other protected or
  irrelevant attributes.
- Identity/contact information is stored separately from evaluation features.
- Institution prestige is **not** scored unless explicitly configured by a recruiter.
- Missing mandatory requirements are surfaced (with “recruiter review recommended”)
  rather than used to silently disqualify.
- A visible disclaimer is shown in the app and in exports.

## Security considerations

See [SECURITY.md](SECURITY.md). Highlights: bcrypt password hashing, JWT auth,
input/upload validation, ORM-based SQL injection prevention, CORS allow-listing,
environment-based secrets, prompt-injection isolation of resume text as untrusted
data, and no secrets in frontend code.

## Deployment

**Easiest:** the Streamlit website — `streamlit_app/app.py`, deployable free on
Streamlit Community Cloud in ~5 minutes (see [DEPLOY.md](DEPLOY.md)).

**Full stack (Docker):**

```bash
cp .env.example .env      # set SECRET_KEY, POSTGRES_PASSWORD, LLM_PROVIDER...
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health
- Demo login: `demo@recruiter.io` / `demo12345`

The backend container runs Alembic migrations, seeds sample data
(5 jobs + 10 resumes), and starts the API. A Celery worker container runs async jobs.

## Project layout

```
resume-screening-system/
├── backend/     FastAPI app (api / core / db / models / schemas / repositories / services / workers / utils)
├── frontend/    React + TS + Tailwind app
├── sample_data/ 5 job descriptions + 10 candidate resumes
├── docker-compose.yml
└── docs: README, ARCHITECTURE, API, DATABASE, ML_PIPELINE, SECURITY
```
