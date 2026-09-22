# Intelligent Resume Screening — Streamlit app

A complete, self-contained recruiting website: create a job, upload PDF/DOCX
resumes, screen and rank candidates with explainable scores, inspect verbatim
evidence, and export a CSV report — all in one page, no separate backend.

## Run locally

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. The app creates its SQLite database and upload
folder automatically under `streamlit_app/data/`.

Tip: click **Load 5 demo jobs + 10 resumes** in the sidebar to see the full
ranking behavior immediately (excellent matches first, weak/gated candidates
flagged for review).

## Deploy to Streamlit Community Cloud (free)

1. Push this repository to GitHub (public or private).
2. Go to <https://share.streamlit.io> → **New app**.
3. Repository: your fork · Branch: `main`.
4. **Main file path:** `streamlit_app/app.py`
5. (Optional) App URL suffix, then **Deploy**.

That's it — no database service, no Docker, no secrets required. First deploy
installs `streamlit_app/requirements.txt` (~2–4 minutes).

### Optional configuration (Advanced settings → Secrets, or environment vars)

| Setting | Effect |
|---|---|
| `EMBEDDING_MODEL` = `sentence-transformers/all-MiniLM-L6-v2` + add `sentence-transformers` to requirements.txt | True semantic embeddings (heavy: pulls in torch; may exceed the free tier's ~1 GB RAM) |
| `LLM_PROVIDER` = `openai`, `OPENAI_API_KEY` = key | Enables GenAI summaries/explanations (never expose keys in code) |

Without these, the app uses a deterministic hashing embedder and rule-based
interview questions — everything else works identically.

## Notes & limits

- If you see ImportError: email-validator is not installed, your environment is missing a declared dependency - run pip install -r requirements.txt inside the app environment (it includes email-validator).

- Data is stored in `streamlit_app/data/rss.db` (SQLite). On Community Cloud
  this resets on app reboot/redeploy — it is a demo-grade store. For
  persistent multi-user deployments use the FastAPI + PostgreSQL stack
  (see `../DEPLOY.md`, Option C).
- One bad resume never breaks the batch: unsupported types, oversized files
  and duplicates are reported inline.
- The decision-support disclaimer is always visible; protected attributes are
  never used in scoring.
