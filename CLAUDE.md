# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

JobScout is an early-stage full-stack application. Backend routes, auth, and models are complete. Frontend is scaffolded with shell pages. Infrastructure (Docker Compose, pre-commit, Alembic) is in place.

## Tech Stack

- **Backend**: FastAPI (Python 3.10+), SQLModel, `uv` package manager, entry point `app.main:app` in `backend/`
- **Frontend**: React 18 (Node.js/npm), Vite, TypeScript, Tailwind CSS, shadcn/ui, Biome linter, dev server at `http://localhost:5173`
- **Type checkers**: both `mypy` and `ty` (Astral) run on the backend — both must pass
- **Database migrations**: Alembic (async) in `backend/migrations/`
- **Email templates**: MJML in `backend/app/email-templates/`
- **E2E tests**: Playwright
- **Frontend API client**: auto-generated from backend's OpenAPI schema (lives in `frontend/src/client/`, do not edit manually)

## Common Commands

```bash
# Backend (run from backend/)
uv run uvicorn app.main:app --reload

uv run ruff check --fix backend/app
uv run ruff format backend/app
uv run mypy app
uv run ty check app

uv run pytest                        # run all backend tests

# Alembic (run from backend/)
uv run alembic upgrade head          # apply all pending migrations
uv run alembic revision --autogenerate -m "describe change"  # generate new migration
uv run alembic downgrade -1          # roll back one migration

# Frontend (run from frontend/)
npm run dev
npm run lint
npm test                             # Vitest unit/component tests
npm run test:e2e                     # Playwright E2E tests

# Regenerate frontend SDK after backend route changes (requires running backend)
bash ./scripts/generate-client.sh
```

## Pre-commit Hooks

Pre-commit enforces: YAML/TOML validation, trailing whitespace, Biome (frontend), Ruff check+format, mypy, ty, and frontend SDK generation (skipped gracefully if backend is not running).

Ruff hooks use `--exit-non-zero-on-fix` — if Ruff auto-fixes anything, the commit is rejected so you can review and re-stage the changes. This is intentional, not a flaky hook.

```bash
# Install hooks (one-time, run from project root)
uvx pre-commit install

# Run hooks manually against changes since origin/main
uvx pre-commit run --from-ref origin/main --to-ref HEAD
```

## Architecture Notes

- The frontend API client (`frontend/src/client/`) is generated from the backend's OpenAPI schema by `scripts/generate-client.sh`. Run after any backend route or schema changes.
- Alembic migrations live in `backend/migrations/`. Always run `alembic upgrade head` before starting the backend against a fresh or updated database.
- `.env` at the project root is used for both local development and VS Code debug configurations.
- Tests use SQLite (`aiosqlite`) — no running database required for the test suite.
