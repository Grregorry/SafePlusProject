# SafePlus Assessment Platform

An AI-enabled health and safety maturity assessment platform, developed as an
R&D project for **First Step Solutions**.

The platform surveys two groups within an organisation — employees and senior
managers — scores their responses against a three-domain maturity model, and
generates audience-specific PDF reports with AI-assisted analysis grounded in
WorkSafe New Zealand's SafePlus guidance.

> **Status:** prototype / research deliverable. Not production-hardened.

## Licensing and intellectual property

Licensing is still to be confirmed. This repository is public from 21 October 2026 so the AUT markers can access it, and will return to private once the project has been marked. Do not copy, reuse or distribute the code until licensing is resolved.

Three parties may hold rights in this work: Auckland University of Technology,
First Step Solutions (client), and WorkSafe New Zealand. The assessment
question set and the curated guidance content in
`backend/app/data/safeplus_guidance.py` derive from WorkSafe's published
SafePlus framework. Confirm ownership and permitted use with your project
supervisor and the client before adding a licence or changing repository
visibility.

## What it does

1. An organisation registers and creates a named assessment.
2. The assessment draws on a 49-question set across three domains
   (Leadership, Worker Engagement, Risk Management). Each question is worded
   twice — once for employees, once for senior managers.
3. Respondents answer via an anonymous public survey link, or results from
   paper surveys are entered as aggregate counts.
4. Responses are scored on a 1–5 scale, producing per-question, per-domain and
   overall maturity levels plus an employee/manager "opinion gap".
5. Google Gemini generates a decision-support analysis, constrained to cite
   only curated WorkSafe guidance sources.
6. Four PDF reports are available: full, business leader, board, and
   operational manager.

See [docs/methodology.md](docs/methodology.md) for the scoring rules and
[docs/data-handling.md](docs/data-handling.md) for what the system stores.

## Architecture

| Layer    | Technology |
|----------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, React Router, Recharts |
| Backend  | FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Database | PostgreSQL |
| Auth     | JWT bearer tokens, Argon2 password hashing |
| AI       | Google Gemini (`gemini-2.5-flash` by default) |
| Reports  | ReportLab (PDF generation) |

## Prerequisites

Install these before setup:

- **Python 3.12 or newer** — `python --version`
- **Node.js 20.19+** (22 or newer recommended) — `node --version`
- **PostgreSQL 14 or newer**, running locally — `psql --version`
- A **Google Gemini API key** from https://aistudio.google.com/apikey
  (optional — the app runs without one, but AI analysis will fail)

## Setup

Five steps, start to finish.

### 1. Create the database

```bash
psql -U postgres -c "CREATE DATABASE \"SafePlusProject\";"
```

### 2. Configure the backend

```bash
cd backend
copy .env.example .env
```

Open `backend/.env` and set:

- `DATABASE_URL` — replace `YOUR_PASSWORD` with your PostgreSQL password
- `JWT_SECRET` — any long random string. Generate one with:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `GEMINI_API_KEY` — your key, or leave as-is to skip AI analysis

The backend will not start without `DATABASE_URL` and `JWT_SECRET`.

### 3. Install backend dependencies

From the `backend` directory:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` includes everything in `requirements.txt` plus the test
tooling. Use `requirements.txt` alone if you do not intend to run the tests.

### 4. Create the database schema

With the virtual environment still active, from `backend`:

```bash
alembic upgrade head
```

This creates all tables **and seeds the three domains and the 49-question
SafePlus question set**. The application will not function without it.

### 5. Install frontend dependencies

From the project root:

```bash
cd frontend
npm install
```

## Running the application

Two servers, two terminals. From the project root:

```bash
backend.bat
```

```bash
frontend.bat
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://127.0.0.1:8000 |
| API docs (Swagger) | http://127.0.0.1:8000/docs |
| Health check | http://127.0.0.1:8000/health |
| Database health check | http://127.0.0.1:8000/database/health |

The landing page renders without the backend running, but every action beyond
it will fail. If pages load but data never appears, check that the backend
started cleanly and that `/database/health` returns `ok`.

### Creating an account

Register at http://localhost:5173/register, then log in. No email provider is
configured in this prototype, so email verification links are returned
directly by the API rather than emailed — use **Resend verification** on the
account page to retrieve yours. This is the documented NFR11 fallback.

## Running the tests

From `backend`, with the virtual environment active:

```bash
pytest
```

Tests require `backend/.env` to exist, because they read `DATABASE_URL` from
it. They then redirect to a **separate database named `safeplus_test`**,
creating it automatically, and assert that they are not pointed at your real
database. Your development data is never touched.

Useful variations:

```bash
pytest tests/test_unit_scoring.py      # one file
pytest -m qa                           # QA-logged tests only
pytest -v                              # verbose
```

Tests marked `qa` emit structured metadata (id, area, title, input, expected)
in their failure output, for use as assessment evidence.

## Project structure

```
SafePlusProject/
├── backend/
│   ├── alembic/versions/      # Migrations, incl. domain + question seeds
│   ├── app/
│   │   ├── api/routes/        # FastAPI endpoints
│   │   ├── core/              # Settings, JWT, password hashing
│   │   ├── data/              # Curated WorkSafe guidance, HSWA references
│   │   ├── db/                # Engine and session
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response models
│   │   └── services/          # Scoring, AI analysis, PDF reports
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/               # Typed backend API clients
│       ├── components/        # Shared UI, maturity scale definitions
│       ├── features/          # Pages by feature area
│       └── layouts/
└── docs/                      # Methodology and data-handling notes
```

## API overview

| Prefix | Purpose |
|--------|---------|
| `/api/auth` | Registration, login, verification, current account |
| `/api/questions` | The SafePlus question set |
| `/api/assessments` | Assessment CRUD, progress, scores, AI analysis, reports |
| `/api/public-surveys` | Anonymous respondent survey flow |

Full interactive documentation at http://127.0.0.1:8000/docs when the backend
is running.

## Troubleshooting

**Backend exits with a `ValidationError` mentioning `database_url`**
`backend/.env` is missing or incomplete. See setup step 2.

**`'.venv\Scripts\activate.bat' is not recognized`**
The virtual environment has not been created. See setup step 3.

**`relation "question" does not exist`**
Migrations have not been run. See setup step 4.

**Frontend shows a blank page or "Failed to fetch"**
The backend is not running, or is on a different port. The frontend defaults
to `http://127.0.0.1:8000`; override with `VITE_API_BASE_URL` in
`frontend/.env`.

**Port 5173 already in use**
Set `PORT` before starting the frontend — `set PORT=5174 && npm run dev`. CORS
already permits any localhost port.

**AI analysis fails**
`GEMINI_API_KEY` is unset or invalid. Scoring and reports work without it.

## Documentation

- [docs/methodology.md](docs/methodology.md) — scoring, maturity thresholds,
  intervention tiers, AI constraints
- [docs/data-handling.md](docs/data-handling.md) — what is stored, anonymity,
  authentication
- [docs/requirements-traceability.md](docs/requirements-traceability.md) —
  requirement references in the codebase