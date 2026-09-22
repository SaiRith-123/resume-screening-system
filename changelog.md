# Changelog

All notable changes to this project are documented here.
Format based on Keep a Changelog; versioning follows SemVer.

## [1.1.1] - 2026-09-15

### Fixed
- **Missing `email-validator` dependency** in `backend/requirements.txt` and
  `streamlit_app/requirements.txt`. `app/schemas/auth.py` uses `EmailStr`, which
  requires `email-validator` at import time, so a from-scratch install crashed with
  `ImportError: email-validator is not installed`. Both files now declare it.
- `app/schemas/__init__.py` now converts a missing `email-validator` into a clear,
  actionable message (`pip install email-validator`) instead of a deep pydantic
  traceback.
- Added an explicit troubleshooting entry to `RUN_VSCODE.md` and
  `streamlit_app/README.md` for this error.

## [1.1.0] - 2026-09-15

### Added
- **Backend hardening**
  - Sliding-window rate limiting on authentication endpoints (`RATE_LIMIT_AUTH` /
    `RATE_LIMIT_DEFAULT`), returning `429` with `Retry-After`.
  - `RequestContextMiddleware`: per-request `X-Request-ID` echo, access logging
    with latency, `X-Process-Time-Ms` header.
  - `SecurityHeadersMiddleware`: `X-Content-Type-Options`, `X-Frame-Options`,
    `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`.
  - GZip response compression (>= 1 KB).
  - `/health/ready` readiness probe with a live database check.
- **API pagination** on `GET /jobs`, `GET /jobs/{id}/candidates`,
  `GET /jobs/{id}/results` via `?page=&page_size=` plus `X-Total-Count`
  (backwards compatible: responses remain arrays).
- **Frontend**
  - Dark mode (class-based Tailwind strategy, persisted, no first-paint flash,
    system-preference default) with a toggle in the sidebar and mobile header.
  - Global `ErrorBoundary` so a render error shows a friendly recovery screen
    instead of a blank page.
  - Skeleton loading state for `DataTable` (used by the Jobs page).
  - Accessibility: labelled theme toggle, `aria-busy`/`role="status"` on
    skeleton state.
  - Vendor chunk splitting (`react`, `charts`) — main bundle reduced from
    ~735 KB to ~162 KB (gzip ~49 KB).
- **Project infrastructure**
  - GitHub Actions CI: backend pytest, frontend `tsc + vite` build, and a
    Streamlit render smoke test.
  - `backend/requirements-ci.txt` — light CI dependency profile.
  - `DEPLOY.md` — Streamlit-first deployment guide (local run + Community
    Cloud) with the full Docker/PostgreSQL stack as the production path.

### Fixed
- Frontend: 32+ source filenames had lowercase-on-disk casing that broke
  case-sensitive builds (`Dockerfile`, hooks, components, pages); all aligned
  with their imports.
- Backend: password hashing now uses the `bcrypt` library directly
  (passlib's backend is incompatible with bcrypt >= 4).
- Resume parser: markdown-style headings (`## Skills`) were not detected, so
  skills were silently missed; academic roles were mis-classified as
  full-time employment.
- LLM JSON helper: retry path could raise `UnboundLocalError`, masking the
  original provider error.
- Frontend: replaced the deprecated `use_container_width` API.

## [1.0.0] - 2026-09-14

### Added
- Initial end-to-end system: FastAPI backend (16 tables, PostgreSQL +
  pgvector, Alembic, JWT auth), multi-strategy matching engine (exact, fuzzy,
  taxonomy-related, semantic, context-aware), deterministic 7-component
  scoring, ranking with eligibility gating, evidence extraction, GenAI
  provider abstraction with prompt-injection defenses, React + TypeScript +
  Tailwind recruiter console, Streamlit website, Docker Compose deployment,
  5 sample jobs + 10 sample resumes, and a 62-test suite.
