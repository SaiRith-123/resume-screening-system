# SECURITY

## Authentication & authorization

- Passwords hashed with **bcrypt** (`app/core/security.py`); input truncated to 72
  bytes for deterministic behaviour. Plaintext is never stored or logged.
- Stateless **JWT** access tokens (HS256, `SECRET_KEY`, configurable expiry).
- Every protected endpoint resolves the current user via an OAuth2 Bearer
  dependency (`app/api/deps.py`); job/candidate access is scoped to the owner.
- Failed login → generic `401` (“Invalid email or password”) to avoid user enumeration.

## Rate limiting

Authentication endpoints (register/login) are protected by a sliding-window
rate limiter (default `20/minute`, configurable via `RATE_LIMIT_AUTH`).
Exceeding it returns `429 Too Many Requests` with a `Retry-After` header.
List endpoints accept `?page=&page_size=` (max 100) to bound response sizes.

## Input & upload validation

- Extension (`.pdf`, `.docx`) **and** MIME allow-listing.
- Size limit (`MAX_UPLOAD_MB`), empty-file rejection.
- Safe filenames: basename + character sanitization + UUID prefix (no path traversal).
- SHA-256 duplicate detection per job.
- All request bodies validated by Pydantic v2 schemas.
- SHA-256 and validated extraction never trust client-declared content types.

## Injection & XSS

- All database access goes through SQLAlchemy ORM with parameter binding — no string
  concatenation of user input into SQL.
- React escapes rendered content by default; no `dangerouslySetInnerHTML` is used.
- Centralized error handling returns structured JSON, never stack traces, to clients.

## CORS & transport

- CORS origins come from `CORS_ORIGINS` (comma-separated allow-list) — never `*`
  in production.
- Every response carries hardening headers: `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, and
  `Cross-Origin-Opener-Policy` (`app/core/middleware.py`). Responses over 1 KB
  are GZip-compressed.
- Deploy behind TLS termination; set `ENVIRONMENT=production`.
- A strict Content-Security-Policy is intentionally applied at the proxy/CDN
  layer (the API itself serves Swagger UI, which needs inline scripts).

## Secrets management

- All secrets via environment variables; `.env.example` documents every variable and
  contains no real values. `.env` is git-ignored.
- **No API keys are shipped to the frontend** — the LLM provider is called only by
  the backend.
- `SECRET_KEY` must be replaced in production.

## LLM / prompt-injection defense (§31)

Resume and JD text is treated as **untrusted data**:

- Prompts separate `SYSTEM INSTRUCTIONS`, `JOB REQUIREMENTS`, and `RESUME DATA`
  with explicit delimiters.
- The system prompt states that instructions inside the resume must never be obeyed.
- `guardrails.detect_injection` flags phrases such as “ignore previous instructions”
  or “rank me first”, and `sanitize_untrusted` neutralizes them before sending.
- LLM output is schema-validated; generated evidence must be a verbatim substring of
  the resume (`is_grounded`) or it is discarded.
- The model can never modify a score; it only explains pre-computed results.

## Bias & privacy protection (§15)

- Scoring excludes gender, age/date of birth, race/ethnicity, religion, marital
  status, photograph, disability, home address, and other protected/irrelevant data.
- Identity/contact information is stored separately from evaluation features.
- Institution prestige is not scored unless explicitly configured.
- Missing mandatory requirements are surfaced for human review; candidates are never
  silently disqualified.
- A visible disclaimer is rendered in the app and included in exports.
- Interview-question generation filters out protected-attribute questions.

## Failure handling (§23)

The system degrades gracefully rather than failing: invalid resume → meaningful
status; empty/scanned PDF → OCR fallback; LLM failure → deterministic results with a
notice; embedding failure → lexical fallback; duplicate resume → rejected with reason.

## Reporting

To report a vulnerability, contact the maintainers privately. Do not open a public
issue containing exploit details.
