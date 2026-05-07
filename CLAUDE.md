# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Speacher — AI 발표 코칭(Presentation Coaching) system. User uploads a presentation video, the backend runs a 7-step analysis pipeline (visual gaze/posture, audio rate/volume/pitch, filler words/pronunciation, GPT feedback) and returns a scored report. Korean is the primary user-facing language; API messages, log strings, and most comments are written in Korean.

## Repository layout

Two independent apps under one repo:

- `backend/` — FastAPI app (`app/main.py`), MySQL via SQLAlchemy 2.0 async, Alembic migrations, Celery + Redis workers, OpenAI/Whisper for analysis. Python 3.11.
- `frontend/` — React 19 + Vite + TailwindCSS, Zustand for auth state, TanStack Query for server state, React Router 7. JavaScript (no TypeScript).

There is no root `package.json`; commands run from inside each subdir.

## Common commands

### Backend (run from `backend/`)

```bash
# First-time setup: start MySQL + Redis (host ports 3307 and 6379)
docker compose up -d

# Install + activate venv (already present at backend/venv on this machine)
pip install -r requirements.txt

# DB migrations
alembic upgrade head
alembic revision --autogenerate -m "message"

# Dev server (http://localhost:8000, docs at /docs when APP_DEBUG=true)
uvicorn app.main:app --reload --port 8000

# Celery worker (Phase 5 pipeline — currently a stub in app/tasks/analysis_task.py)
celery -A app.tasks.celery_app.celery_app worker -l info

# Tests (pytest is installed but tests/ is empty as of this commit)
pytest
pytest tests/path/to/test_file.py::test_name
```

`backend/.env` must exist; copy from `backend/.env.example`. Note that `docker-compose.yml` exposes MySQL on host port **3307** while `.env.example` defaults `DB_PORT=3306` — adjust `DB_PORT` to `3307` when connecting from the host.

### Frontend (run from `frontend/`)

```bash
npm install
npm run dev      # Vite dev server on :5173
npm run build
npm run lint     # ESLint flat config (eslint.config.js)
npm run preview
```

`frontend/.env` sets `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api/v1`).

## Architecture

### Request/response contract

Every successful API response is wrapped in `SuccessResponse` (`backend/app/schemas/common.py`):

```json
{ "success": true, "data": {...}, "message": "..." }
```

Errors are wrapped by `register_error_handlers` in `backend/app/middleware/error_handler.py`:

```json
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }
```

The frontend axios layer (`frontend/src/api/axiosInstance.js`) and stores rely on this shape — preserve it when adding endpoints.

There are **two parallel exception systems**: domain exceptions in `app/core/exceptions.py` (`SpeacherException`, `NotFoundException`, etc.) and the registered handlers in `app/middleware/error_handler.py`. `main.py` only calls `register_error_handlers`, so `SpeacherException` subclasses are caught by the generic `Exception` handler and returned as 500. If you raise a domain exception and need a specific status code, either register `core/exceptions.register_exception_handlers(app)` in `main.py` or raise `HTTPException` directly.

### Backend layering

Routes → services → CRUD → models. Don't put DB queries in routers, and don't put business rules in CRUD.

- `app/api/v1/` — routers, mounted under `/api/v1` by `router.py` (`auth`, `analysis`).
- `app/services/` — business logic. Singleton instances (`auth_service`, `analysis_service`) imported by routers.
- `app/crud/` — pure DB read/write helpers, take `db: AsyncSession`.
- `app/models/` — SQLAlchemy 2.0 declarative models with `Mapped[...]` typing. All registered via `app/models/__init__.py` so Alembic autogenerate sees them.
- `app/schemas/` — Pydantic request/response models.
- `app/utils/dependencies.py` — `get_current_user` is the auth dependency; uses `HTTPBearer` + `app/utils/jwt.py`.
- `app/middleware/rate_limit.py` — in-memory dict-based limiter (`login_rate_limit`, `register_rate_limit`, `refresh_rate_limit`); resets on restart, not Redis-backed despite `slowapi` being installed.
- `app/db/session.py` — `get_db` async generator commits on success and rolls back on exception. Don't `await db.commit()` inside services unless you understand this.

### Analysis domain

Core workflow lives in three models linked by FK with `cascade="all, delete-orphan"`:

- `AnalysisJob` — one per upload, tracks `JobStatus` (PENDING/PROCESSING/COMPLETED/FAILED), `current_step` (1–7), `step_progress` (0–100), and `celery_task_id`.
- `AnalysisResult` — scores and GPT feedback (one-to-one with job).
- `TimelineEvent` — per-event timeline entries (gaze break, filler word, etc.).

The 7-step pipeline (`ANALYSIS_STEPS` in `frontend/src/constants/index.js`) and 7-metric scoring rubric (`SCORE_*` in `app/config.py`, mirrored in `SCORE_WEIGHTS` on the frontend) are duplicated client/server — **keep them in sync** when changing weights or steps.

The actual Celery pipeline (`app/tasks/analysis_task.py`, `app/services/analysis/`) is a Phase 5 stub; `analysis_service.start_analysis` creates the job and saves the file but does not yet dispatch to Celery (commented-out block in `services/analysis_service.py:67-75`).

### Frontend conventions

- **Auth**: `stores/authStore.js` (Zustand + persist) holds user/auth flag. Tokens themselves live in `localStorage` under `speacher_access_token` / `speacher_refresh_token` (constants in `src/constants/index.js`), not in the persisted Zustand slice. `axiosInstance.js` auto-attaches the access token and transparently refreshes on 401 with a queued-request pattern — don't bypass it for authed requests.
- **Routing**: All app routes are guarded by `PrivateRoute` / `PublicRoute` in `App.jsx`, gated on `isAuthenticated`. The auth page lives at `/`.
- **Server state**: Use TanStack Query via the hooks in `src/hooks/` (`useAuth`, `useAnalysis`). Query client config (1 retry, no refetch-on-focus, 60 s stale) is in `main.jsx`.
- **Polling**: `POLLING_INTERVAL_MS = 2000` is used by `AnalyzingPage` to poll `/analysis/{job_id}/status` until COMPLETED/FAILED.
