# BrandShield

BrandShield is a Digital Risk Protection platform foundation. Future stages will monitor impersonating social profiles and applications; this repository deliberately contains none of that detection or dashboard functionality yet.

## Architecture

`React + TypeScript (Vite, :5173)` → `FastAPI (:8000)` → `PostgreSQL (Docker Compose, :5432)`.

The backend runs only from a repository-local Python 3.13 `.venv`. Alembic is configured for future schema changes. The frontend requests `GET /api/health` using `VITE_API_BASE_URL`; the API checks PostgreSQL before reporting a connected database.

## Prerequisites

- Node.js 24 LTS and npm
- Docker Desktop with Docker Compose
- Python **3.13** registered with the Windows launcher (`py`)

Do not install native PostgreSQL: the development database runs only through Docker Compose. Python 3.14 may remain installed globally; it is not used for this project.

## First-time setup

> Validation note: the frontend install, development server, and production build were validated when this foundation was created. The Python, Docker, migration, and API commands below are the required repeatable commands, but were not run in this checkout because Python 3.13 was unavailable through `py` and Docker Desktop's engine was stopped.

1. Copy `.env.example` to `.env`, then set a unique local `POSTGRES_PASSWORD` and make the password in `DATABASE_URL` match. `.env` is ignored by Git.
2. Confirm the required interpreter: `py --list`.
3. Create the project environment: `py -3.13 -m venv .venv`.
4. Activate it: `.venv\Scripts\activate`.
5. Confirm `python --version` is Python 3.13.x and `python -m pip --version` points inside `BrandShield\.venv`.
6. Install backend dependencies: `python -m pip install -e ".\backend[dev]"`.
7. Install frontend dependencies: `npm install --prefix frontend`.

## Run locally

Start PostgreSQL and wait for it to become healthy:

```powershell
docker compose up -d postgres
docker compose ps
```

Run the domain migration history, from `backend`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
```

Seed deterministic, clearly synthetic demo records (safe to run repeatedly):

```powershell
..\.venv\Scripts\python.exe -m app.seed
```

Start the API, from `backend`:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

In another terminal, start the frontend:

```powershell
npm run dev --prefix frontend
```

Open `http://localhost:5173`. It displays the actual response from `http://localhost:8000/api/health`. Test the same endpoint in Postman with a GET request. A connected database returns `{"status":"ok","database":"connected"}`; an unreachable database returns a machine-readable degraded state.

Build the frontend with `npm run build --prefix frontend`. Run backend tests from `backend` using `..\.venv\Scripts\python.exe -m pytest`.

Stop the database with `docker compose down`; add `--volumes` only when intentionally discarding local database data. View logs with `docker compose logs postgres`.

## DBeaver

Use a normal PostgreSQL connection: host `localhost`, port from `POSTGRES_PORT` (default `5432`), database/user/password from your local `.env`. DBeaver is optional and is not needed at runtime.

## Repository layout

- `frontend/` — React/Vite UI shell and API client
- `backend/` — FastAPI, SQLAlchemy session, and Alembic infrastructure
- `data/` — future controlled seed/demo data
- `docs/`, `scripts/` — documentation and automation space

## Current scope

Implemented: health reporting, configuration, CORS, database connectivity plumbing, Compose PostgreSQL, Alembic migrations, and a queryable Brand domain layer.

## Brand domain API

All records below are local, controlled demo data; they are not scraped, live, or risk-scored.

- `GET` / `POST` `/api/brands`
- `GET` `/api/brands/{id}` and `/api/brands/{id}/assets`
- `GET` / `POST` `/api/brands/{id}/social-accounts`
- `GET` / `POST` `/api/brands/{id}/apps`
- `GET` / `POST` `/api/brands/{id}/social-candidates`
- `GET` / `POST` `/api/brands/{id}/app-candidates`

The migration adds `brands`, `official_social_accounts`, `official_apps`, `official_brand_assets`, `social_candidates`, and `app_candidates`. DBeaver can inspect these tables using the existing local connection. Candidate rows remain observations (`NEW`, `REVIEWED`, or `IGNORED`) and intentionally carry no threat, risk, or confidence score.

## Detection API

The deterministic local engine persists one current analysis per candidate, with ordered structured evidence. Exact official-asset matches are always `SAFE`; remote logo URLs are explicitly reported as unavailable rather than assigned a fabricated score.

- `POST` `/api/analyze/name`
- `POST` `/api/analyze/social/{candidate_id}`
- `POST` `/api/analyze/app/{candidate_id}`
- `POST` `/api/detections/scan`
- `GET` `/api/detections` and `GET` `/api/detections/{id}`

Scores use available name, look-alike, description, and publisher signals. A similarity-only outcome is capped below `MEDIUM`; the score is not a statistical confidence measure. No LLM, external API, or live scraping is used.

Not implemented: scraping, live monitoring, authentication, dashboard UI, and production deployment.
