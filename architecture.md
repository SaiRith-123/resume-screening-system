# ARCHITECTURE

## 1. Overview

The system is a layered web application with a React SPA frontend and a FastAPI
backend backed by PostgreSQL + pgvector. All resume-processing is orchestrated by
a deterministic service pipeline; GenAI is a strictly additive explanation layer.

```
┌──────────────────────────┐        ┌──────────────────────────────┐
│  React SPA (Vite, TS)    │  HTTP  │  FastAPI application          │
│  Tailwind, Router, Axios │ ─────▶ │  api → repositories/services  │
│  Recharts, Dropzone      │        │  core / db / schemas          │
└──────────────────────────┘        └───────────────┬──────────────┘
                                                     │ SQLAlchemy
                                        ┌────────────▼────────────┐
                                        │ PostgreSQL + pgvector   │
                                        └────────────▲────────────┘
                                                     │
                                        ┌────────────┴────────────┐
                                        │ Celery worker (Redis)   │
                                        │ resume + screening jobs │
                                        └─────────────────────────┘
```

## 2. Backend layering (clean architecture)

| Layer | Package | Responsibility |
|---|---|---|
| API | `app/api` | HTTP routers, request/response models, dependency-injected auth |
| Core | `app/core` | Config, logging, security (bcrypt/JWT), centralized errors |
| DB | `app/db` | Declarative base, session factory, portable column types, bootstrap, seed |
| Models | `app/models` | SQLAlchemy ORM (16 tables) |
| Schemas | `app/schemas` | Pydantic v2 contracts (validation boundary) |
| Repositories | `app/repositories` | Data access; the only layer that talks to the ORM session |
| Services | `app/services` | Business logic (see below) |
| Workers | `app/workers` | Celery app, tasks, candidate state machine |
| Utils | `app/utils` | File validation/safe storage, text cleaning |

Service sub-packages:

```
services/
  resume_parser/     extractor (PDF/DOCX), ocr, section_detector, resume_structurer
  jd_parser/         jd_structurer (requirements + responsibilities separation)
  skill_matcher/     taxonomy, normalizer, matcher (exact/fuzzy/semantic/related/context)
  embedding_service/ embedder (sentence-transformers, hashing fallback)
  scoring_engine/    weights, experience, education, scorer
  screening/         pipeline, evidence, ranking
  processing.py      resume ingestion orchestration
  llm_service/       provider, providers, prompts, guardrails, genai
```

**Rule:** routers never contain business logic; services never import routers;
repositories are the only place that opens queries.

## 3. Processing pipeline

1. **Upload** — validated (extension, MIME, size), safely named, hashed (SHA-256)
   for duplicate detection, stored under `storage/uploads/job_<id>/`.
2. **Extraction** — pdfplumber → pypdf fallback → OCR fallback (pdf2image + tesseract).
   Returns an `ExtractionResult` describing method and errors; never raises on a
   malformed file.
3. **Section detection → structuring** — deterministic extraction merges with an
   optional LLM pass and is validated by `ResumeSchema`.
4. **Normalization** — skills mapped to a canonical taxonomy; related-but-distinct
   technologies get partial credit only.
5. **Matching** — exact → fuzzy → semantic → related, with context-aware evidence
   strength (experience > project > summary > list).
6. **Scoring** — seven 0–100 components combined by configurable weights.
7. **Ranking** — sort by (eligibility, score); gated candidates are flagged, never dropped.
8. **Evidence** — quoted verbatim from the resume; ungrounded text is discarded.
9. **GenAI** — summary / explanation / interview questions, schema-validated.

## 4. Concurrency & state management

Candidate states: `UPLOADED → PROCESSING → EXTRACTED → ANALYZED → SCREENED`
(with `FAILED` reachable from any state and recoverable). Transitions are defined in
`app/workers/states.py`. Jobs are dispatched to Celery when a broker is configured,
otherwise they run inline so the app works without Redis.

## 5. Error handling & graceful degradation

- App errors (`AppError` hierarchy) → structured JSON with `{error:{code,message}}`.
- Validation errors → HTTP 422 with detail.
- One malformed resume never fails the batch (per-candidate try/except).
- If embeddings fail → semantic component falls back to 0 / token overlap.
- If the LLM is unavailable → deterministic results still returned, with
  “AI explanation unavailable. Deterministic screening results are still available.”

## 6. Frontend architecture

- `api/client.ts` — Axios instance with JWT interceptor and 401 handling.
- `hooks/` — `useAuth`, `useJobs`, `useCandidates`, `useScreening`.
- `layouts/` — `AppLayout` (sidebar shell), `AuthLayout` (centered auth).
- `components/` — reusable UI: DataTable, ScoreChart, ScoreBreakdownPanel,
  EligibilityBanner, EvidencePanel, UploadDropzone, ProgressTracker, states, dialogs.
- `pages/` — Dashboard, JobList, JobCreate, JobDetail, Ranking, CandidateDetail,
  Search, Login, Register, NotFound.

## 7. Why the LLM does not compute the score

Making a model responsible for a hiring decision is opaque, unreproducible, and
hard to audit. Instead the score is computed by an explicit, testable algorithm;
the LLM only *explains* already-computed results and can never change them.
