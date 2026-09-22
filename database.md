# DATABASE

PostgreSQL 16 with the **pgvector** extension. Schema is managed by Alembic
(`backend/alembic/`), and can also be created by `app.db.init_db` on boot.

## Tables

### `users`
| column | type | notes |
|---|---|---|
| id | serial PK | |
| email | varchar(255) | unique, indexed (lower) |
| full_name | varchar(255) | |
| hashed_password | varchar(255) | bcrypt |
| role | varchar(32) | default `recruiter` |
| is_active | boolean | default true |
| created_at / updated_at | timestamptz | |

### `jobs`
| column | type | notes |
|---|---|---|
| id | serial PK | |
| owner_id | FK users(id) ON DELETE CASCADE | indexed |
| title | varchar(255) | indexed |
| department/seniority/location/employment_type | varchar | |
| description | text | |
| weights | jsonb | per-job scoring weights |
| hard_gate | boolean | treat missing mandatory as a gate |
| status | varchar(32) | default `open` |

Index: `(owner_id, status)`

### `job_requirements`
`id`, `job_id` (FK, indexed), `kind` (skill|experience|education|certification|technology),
`priority` (required|preferred), `value`, `normalized_value`, `min_years`, `is_hard_gate`, `weight`.
Index: `(job_id, kind, priority)`

### `candidates`
`id`, `job_id` (FK, indexed), `name` (indexed), `email`, `phone`, `summary`,
`total_experience_years`, `status`, `processing_error`, `structured` (jsonb).
Indexes: `(job_id, status)`, `(job_id, name)`.

> Identity/contact columns are deliberately separate from evaluation features (§15).

### `resumes`
`id`, `candidate_id` (FK), `original_filename`, `stored_path`, `content_type`,
`size_bytes`, `sha256` (indexed), `extracted_text`, `extraction_method`, `page_count`.
Index: `(candidate_id, sha256)` for duplicate detection.

### `skills`
`id`, `canonical_name` (unique), `category`, `aliases`.

### `candidate_skills`
`id`, `candidate_id` (FK), `skill_id` (FK, nullable), `raw_name`, `normalized_name`,
`category`, `evidence_context` (list|summary|experience|project|certification),
`evidence_strength`.
Indexes: `(candidate_id, normalized_name)` unique, plus lookup index.

### `experiences`
`id`, `candidate_id` (FK), `company`, `title`, `description`, `start_date`, `end_date`,
`is_current`, `kind` (internship|full-time|freelance|academic), `duration_months`.

### `education`
`id`, `candidate_id` (FK), `degree`, `field_of_study`, `institution`, `start_year`, `end_year`, `grade`.

### `projects`
`id`, `candidate_id` (FK), `name`, `description`, `technologies` (jsonb).

### `certifications`
`id`, `candidate_id` (FK), `name`, `issuer`, `year`.

### `embeddings`
`id`, `owner_type` (candidate|job|resume|evidence), `owner_id`, `field`,
`model_name`, `dim`, `vector` (**vector(384)** via pgvector).
Indexes: `(owner_type, owner_id, field)`; add an HNSW/IVFFlat index for large corpora:
```sql
CREATE INDEX ON embeddings USING hnsw (vector vector_cosine_ops);
```

### `screening_results`
Stores **every component separately** (never only the final score):
`skill_score, experience_score, semantic_score, education_score, project_score,
certification_score, preferred_score, final_score, weights (jsonb), rank,
eligibility_status, missing_requirements (jsonb), matched_skills, partial_skills,
missing_skills, recommendation, needs_review, llm_explanation (jsonb)`.
Indexes: `(job_id, final_score)`, `(job_id, rank)`.

### `screening_evidence`
`id`, `result_id` (FK), `requirement`, `requirement_kind`, `status`, `confidence`,
`evidence_text` (verbatim resume substring), `source`.

### `interview_questions`
`id`, `candidate_id` (FK), `job_id` (FK), `kind` (technical|project|behavioral|role),
`question`, `rationale`, `source`.
Index: `(candidate_id, job_id)`.

## Relationships

```
users 1─* jobs 1─* job_requirements
                1─* candidates
candidates 1─* resumes
           1─* candidate_skills ─1 skills
           1─* experiences
           1─* education
           1─* projects
           1─* certifications
           1─* screening_results ─* screening_evidence
           1─* interview_questions
embeddings (owner_type, owner_id) → jobs | candidates | resumes
```

## Migrations

```bash
cd backend
alembic upgrade head          # apply
alembic revision --autogenerate -m "message"   # new revision
alembic downgrade -1          # roll back one
```

`alembic/versions/0001_initial.py` enables the `vector` extension and creates all
tables from the ORM metadata.

## Notes on portability

JSON columns use `JSONType` (JSONB on PostgreSQL, JSON elsewhere) and the vector
column uses `VectorType` (pgvector on PostgreSQL, binary elsewhere) so the same
models run in SQLite-based tests without PostgreSQL.
