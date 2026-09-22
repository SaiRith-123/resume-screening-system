# API REFERENCE

Base URL: `/api`  ·  All endpoints except `auth/register` and `auth/login` require
`Authorization: Bearer <token>`. Auth endpoints are rate-limited: exceeding the
limit returns **429** with a `Retry-After` header (configurable via
`RATE_LIMIT_AUTH` / `RATE_LIMIT_DEFAULT`).

Errors use a consistent shape:

```json
{ "error": { "code": "validation_error", "message": "Invalid request", "details": {} } }
```

| Status | Meaning |
|---|---|
| 200/201 | Success |
| 401 | Missing/invalid token |
| 403 | Forbidden |
| 404 | Not found |
| 422 | Validation / processing error |
| 500 | Unexpected error |

---

## Auth

### `POST /api/auth/register`
Body: `{ "email", "full_name", "password" }` (password ≥ 8 chars) → **201**

```json
{ "access_token": "…", "token_type": "bearer", "user": { "id": 1, "email": "…", "full_name": "…", "role": "recruiter", "created_at": "…" } }
```

### `POST /api/auth/login`
Body: `{ "email", "password" }` → **200** `Token` (as above). **401** on bad credentials.

---

## Jobs

### `POST /api/jobs` → **201** `Job`
```json
{
  "title": "Machine Learning Engineer",
  "description": "…",
  "department": "AI", "seniority": "Mid", "location": "Remote", "employment_type": "Full-time",
  "requirements": [
    { "kind": "skill", "priority": "required", "value": "Python", "is_hard_gate": true },
    { "kind": "skill", "priority": "preferred", "value": "PyTorch" },
    { "kind": "experience", "priority": "required", "value": "experience", "min_years": 2 },
    { "kind": "education", "priority": "required", "value": "Bachelor's degree in Computer Science" }
  ],
  "weights": { "skill": 0.35, "experience": 0.2, "semantic": 0.15, "education": 0.1, "project": 0.1, "certification": 0.05, "preferred": 0.05 },
  "hard_gate": false,
  "parse_with_llm": true
}
```
If `requirements` is omitted and `parse_with_llm` is true, requirements are derived
from the description (deterministic parser + LLM when configured).

### `GET /api/jobs` → **200** `JobListItem[]`
Each item: `id, title, status, created_at, candidate_count, average_match, top_candidate`.
Paginated: `?page=1&page_size=50` (max 100) with the full count in the
`X-Total-Count` response header. Response shape stays a plain array.

### `GET /api/jobs/{id}` → **200** `Job` (with `requirements`) · **404**

### `PUT /api/jobs/{id}` → **200** `Job` (partial update; `weights` re-normalized to 1.0)

### `DELETE /api/jobs/{id}` → **200** `{ "message": "Job deleted" }`

---

## Resumes & screening

### `POST /api/jobs/{id}/resumes` (multipart)
Form fields: `files` (repeatable), query `auto_screen` (default `true`).

```json
{
  "accepted": [ { "candidate_id": 12, "filename": "cv.pdf", "status": "SCREENED" } ],
  "rejected": [ { "filename": "notes.txt", "reason": "unsupported_file_type:.txt" } ],
  "screened": 1
}
```
Rejection reasons include `unsupported_file_type`, `unsupported_mime_type`,
`file_too_large`, `empty_file`, `duplicate_resume`.

### `GET /api/jobs/{id}/candidates` → **200** `CandidateListItem[]`
Paginated: `?page=&page_size=` + `X-Total-Count` (same contract as `/jobs`).

### `POST /api/jobs/{id}/screen` (optional body: `[candidate_ids]`) → **200** `{ "screened": N }`

### `GET /api/jobs/{id}/results` → **200** `ScreeningResult[]`
Paginated: `?page=&page_size=` + `X-Total-Count` (same contract as `/jobs`).
```json
{
  "id": 5, "candidate_id": 12, "job_id": 3, "rank": 1,
  "eligibility_status": "MEETS_ALL_MANDATORY", "recommendation": "strong_match", "needs_review": false,
  "missing_requirements": [], "matched_skills": ["Python", "SQL"],
  "partial_skills": ["Docker"], "missing_skills": ["AWS"],
  "scores": { "skill_score": 91, "experience_score": 85, "semantic_score": 88, "education_score": 100,
              "project_score": 80, "certification_score": 70, "preferred_score": 75,
              "final_score": 87.4, "weights": { "skill": 0.35, … } },
  "evidence": [ { "requirement": "Python", "requirement_kind": "skill", "status": "MATCH",
                  "confidence": 0.94, "evidence_text": "Developed backend services using Python and FastAPI.", "source": "resume" } ],
  "explanation": null
}
```

### `GET /api/jobs/{id}/export?fmt=csv|xlsx|pdf` → file download
Columns: Candidate, Overall Score, Eligibility, Matched Skills, Missing Skills,
Experience, Education, Recommendation.

---

## Candidates

### `GET /api/candidates/{id}` → **200** `CandidateDetail`
Includes `structured` (the validated §5 schema) and the latest `screening` result.

### `GET /api/candidates/{id}/resume` → original resume file download

### `GET /api/candidates/{id}/explanation` → **200** GenAI explanation
```json
{ "summary": "…", "strengths": [], "weaknesses": [],
  "matched_requirements": [], "missing_requirements": [], "evidence": [], "confidence": 0.91, "available": true }
```
When no provider is configured: `{ "available": false, "note": "AI explanation unavailable. Deterministic screening results are still available." }`

### `POST /api/candidates/{id}/interview-questions` → **200**
```json
{ "candidate_id": 12, "job_id": 3, "available": true,
  "technical": [], "project": [], "behavioral": [], "role": [], "stored": [] }
```

---

## Search

### `GET /api/search/candidates?q=&job_id=&min_score=&experience_min=`
- Without `q`: keyword/filter mode ordered by final score.
- With `q`: **semantic** mode — candidates embedded and ranked by cosine similarity.

```json
{ "query": "strong backend with Python APIs", "mode": "semantic",
  "results": [ { "candidate_id": 12, "job_id": 3, "name": "…", "final_score": 87.4,
                 "semantic_score": 82.1, "eligibility_status": "MEETS_ALL_MANDATORY",
                 "total_experience_years": 4.0, "missing_requirements": [] } ] }
```

---

## Meta

- `GET /health` → `{ "status": "ok", … }`
- `GET /health/ready` → **200** `{ "status": "ok", "database": "ok" }` or **503** when the DB is unreachable (use for probes)
- `GET /` → app metadata + disclaimer
- `GET /docs` → Swagger UI · `GET /openapi.json` → OpenAPI schema

Every response carries `X-Request-ID` (echo it for support) and
`X-Process-Time-Ms`; responses over 1 KB are GZip-compressed.
