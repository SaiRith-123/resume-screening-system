# ML / NLP PIPELINE

## 1. Text extraction

| Source | Primary | Fallback | Notes |
|---|---|---|---|
| PDF | `pdfplumber` | `pypdf`, then OCR | OCR via `pdf2image` + `pytesseract` when text < 120 chars |
| DOCX | `python-docx` | — | paragraphs + tables |

Validation happens before extraction: extension (`.pdf`, `.docx`), MIME, size
(`MAX_UPLOAD_MB`), non-empty, SHA-256 duplicate check. Failures produce a status,
never a crash.

## 2. Section detection

Heading-based segmentation into summary, skills, experience, education, projects,
certifications, contact, languages, awards. Handles plain and `:`-terminated headings
and common aliases ("Work Experience", "Professional Experience", …).

## 3. Structured extraction (§5 schema)

Deterministic extraction runs first (regex for email/phone/years/date ranges;
section parsing for skills/experience/education/projects/certifications). An optional
LLM pass **only fills empty fields** and never overwrites deterministic findings.
Output is validated by `ResumeSchema` (Pydantic v2).

## 4. Skill normalization & taxonomy

Canonical library with aliases and categories. Examples:

```
Postgres → PostgreSQL   ReactJS → React   Node → Node.js
JS → JavaScript         PyTorch framework → PyTorch   REST API development → REST APIs
```

Relatedness (0–1) gives partial credit inside a family but keeps distinct
technologies distinct:

| Pair | Relatedness |
|---|---|
| PostgreSQL ↔ MySQL | 0.40 |
| PyTorch ↔ TensorFlow | 0.50 |
| AWS ↔ GCP | 0.40 |
| Python ↔ Java | 0.10 (explicit unrelated) |
| React ↔ Angular | 0.10 (explicit unrelated) |
| PostgreSQL ↔ MongoDB | 0.10 (explicit unrelated) |
| AWS ↔ Azure | 0.10 (explicit unrelated) |

## 5. Matching strategies

| Strategy | Method | Threshold |
|---|---|---|
| Exact | normalized equality | 1.0 |
| Fuzzy | RapidFuzz token-set ratio | MATCH ≥ 88, PARTIAL ≥ 74 |
| Semantic | cosine similarity (embeddings) | MATCH ≥ 0.72, PARTIAL ≥ 0.55 |
| Related | taxonomy relatedness | PARTIAL ≥ 0.40 |

**Contextual evidence strength (§8D).** Confidence is scaled by *where* a skill
appears:

```
experience 1.00 > project 0.85 > certification 0.70 > summary 0.60 > skills list 0.50
```

```
Skills section:  Python                                   → weaker evidence
Experience:      "Built production APIs using Python."    → stronger evidence
```

## 6. Embeddings

- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim), normalized, cosine similarity.
- Embedded targets: job description + responsibilities, required/preferred skills,
  candidate summary, experience, projects.
- Default runtime: the transformer model is required and failures are surfaced.
  A deterministic hashing encoder is available only when explicitly selected with
  `EMBEDDING_BACKEND=hash` for degraded tests or offline diagnostics.

Similarity is stretched around a 0.25 baseline before mapping to 0–100 so unrelated
text is not over-credited.

## 7. Experience calculation

- Intervals built from start/end dates; **overlapping jobs merged** (no double counting).
- `academic` classified entries are excluded from professional experience.
- `internship` / `freelance` / `full-time` retained and used for scoring.
- Missing end + `is_current` → today; partial dates handled conservatively.

## 8. Education matching

Degree-level ranking (PhD > Master > Bachelor > Diploma) with field synonym matching
(CS/CSE/computing; IT/information systems; …). Institution prestige is never scored
unless a recruiter explicitly configures it.

## 9. Scoring

```
skill          35%   share of required skills matched (status-weighted)
experience     20%   smooth curve vs. minimum years
semantic       15%   embedding cosine similarity
education      10%   degree + field match
project        10%   project↔job semantic relevance (needs ≥1 project)
certification   5%   required certifications matched
preferred       5%   preferred requirements matched

final_score = Σ component × weight      (weights normalized to 1.0)
```

Status credit: `MATCH=1.0`, `PARTIAL_MATCH=0.55`, `MISSING=0.0`, `UNKNOWN=0.35`
(before contextual scaling).

## 10. Evidence & explainability

Each important match carries an `evidence_text` that is a **verbatim substring** of
the resume (sentence-level search). GenAI-produced evidence is validated against the
resume and dropped if ungrounded (`is_grounded`). The final score is always shown as
a component table so the derivation is fully visible.

## 11. GenAI layer

- Provider abstraction: `LLMProvider.generate(prompt)` with `generate_json`
  (parse + Pydantic validation + up to 3 retries).
- Providers: OpenAI-compatible, generic chat-completions HTTP, local (Ollama/vLLM),
  and a `NullProvider` for graceful degradation.
- Safety: resume text is wrapped in `===RESUME DATA===` delimiters and treated as
  untrusted data; injection phrases are neutralized; sensitive-attribute questions
  are filtered out.
- The LLM never changes a score and never invents experience (returns `UNKNOWN`).
