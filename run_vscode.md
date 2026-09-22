# Running the project in VS Code

Two ways to run it. Start with **Option 1** (one process, works immediately).
The `.vscode/` folder already contains launch configs, tasks and recommended
extensions, so most of this is a couple of clicks.

---

## Option 1 — Streamlit website (fastest, no services)

**One-time setup**

1. Open the project folder in VS Code (`File → Open Folder…`).
2. Open a terminal (`` Ctrl+` ``) and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
pip install -r streamlit_app/requirements.txt
```

3. Set the interpreter: `Ctrl+Shift+P` → **Python: Select Interpreter** → pick `.venv`.
4. Install the recommended extensions when VS Code prompts (or run
   **Extensions: Show Recommended Extensions**).

**Run it**

- Press **F5** and choose **“Streamlit: Run website (recommended)”**, or
- Run the task **Terminal → Run Task… → `streamlit: run website`**, or
- Just type `streamlit run streamlit_app/app.py` in the terminal.

Browser opens at <http://localhost:8501>. Click **Load 5 demo jobs + 10 resumes**
in the sidebar to see the ranking immediately.

---

## Option 2 — React frontend + FastAPI backend

This runs the two real apps side by side (the backend uses **SQLite**, so no
PostgreSQL needed for local development).

**One-time setup** (two terminals, or one after the other)

```powershell
# Terminal 1 — backend
cd backend
pip install -r requirements.txt

# Terminal 2 — frontend
cd frontend
npm install
```

Point the frontend at the local API — create `frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000/api
```

**Run it**

- Backend: **F5** → **“Backend: FastAPI (SQLite, no services needed)”**
  (Swagger UI at <http://localhost:8000/docs>).
- Frontend: **Terminal → Run Task… → `dev: frontend (vite)`**, or `npm run dev`
  in `frontend/` (<http://localhost:5173>).
- Seed demo data once: task **`backend: migrate + seed (SQLite)`**.

Log in with `demo@recruiter.io` / `demo12345` after seeding.

---

## Handy tasks (Ctrl+Shift+P → “Tasks: Run Task”)

| Task | What it does |
|---|---|
| `setup: install backend deps` | `pip install -r backend/requirements.txt` |
| `setup: install frontend deps` | `npm install` in `frontend/` |
| `setup: install streamlit deps` | `pip install -r streamlit_app/requirements.txt` |
| `backend: migrate + seed (SQLite)` | Creates tables + loads 5 jobs / 10 resumes |
| `backend: tests` | Runs the 70-test pytest suite |
| `backend: run (reload)` | Uvicorn with auto-reload on port 8000 |
| `dev: frontend (vite)` | Vite dev server on port 5173 |
| `frontend: build (type-check included)` | `tsc -b && vite build` (also run with `Ctrl+Shift+B`) |
| `streamlit: run website` | The Streamlit app |
| `full stack: docker compose up` | PostgreSQL + Redis + backend + worker + frontend |

**Debugging:** set breakpoints in any `.py` file and press F5 with the backend or
pytest config; VS Code's debugger attaches automatically (`debugpy`).

---

## Option 3 — the real production stack (Docker)

Only needed when you want PostgreSQL + pgvector + Celery:

```powershell
copy .env.example .env      # then edit SECRET_KEY and passwords
docker compose up --build
```

Frontend <http://localhost:5173>, API <http://localhost:8000/docs>.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | You are running from the wrong folder — the backend must run with `backend/` as the working directory (the F5 config already does this), or add `"python.analysis.extraPaths": ["./backend"]` (already in `.vscode/settings.json`). |
| PowerShell blocks `Activate.ps1` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once. |
| Frontend shows a network/CORS error | Make sure `frontend/.env` has `VITE_API_BASE_URL=http://localhost:8000/api` and the backend is running; restart `npm run dev` after editing `.env`. |
| `sqlite3.OperationalError` on the backend | The SQLite file is created next to `backend/`; delete `backend/local_dev.db` and re-run the seed task. |
| Streamlit says port 8501 in use | `streamlit run streamlit_app/app.py --server.port 8502`. |
| `ImportError: email-validator is not installed` | Your venv is missing a dependency added in v1.1.1 — run `pip install -r streamlit_app/requirements.txt` (or `pip install email-validator`) inside the activated venv, then restart. |
| Tests can't import packages | Activate the venv first: `.\.venv\Scripts\Activate.ps1`. |

---

## Which files to edit

| I want to change… | Edit |
|---|---|
| Streamlit page text / default job | `streamlit_app/app.py` (`main()` and the form defaults) |
| Streamlit theme/colors | `streamlit_app/.streamlit/config.toml` |
| React page content | `frontend/src/pages/*.tsx` |
| React colors/theme | `frontend/tailwind.config.js`, `frontend/src/index.css` |
| API endpoints | `backend/app/api/v1/*.py` |
| Scoring weights | `backend/app/services/scoring_engine/weights.py` |
| Skill taxonomy | `backend/app/services/skill_matcher/taxonomy.py` |
| Demo data | `sample_data/job_descriptions/`, `sample_data/resumes/` |
