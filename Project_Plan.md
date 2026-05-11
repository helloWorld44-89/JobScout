# JobScout – Project Plan

## Overview

JobScout is a self-hosted web application that automates job hunting. It scrapes job listings on demand, scores them against your personal criteria, and uses AI to generate tailored resumes and cover letters for high-scoring matches. The result: a notification and ready-to-send documents waiting for you.

## Core Features

1. **Job Scraping** – Search LinkedIn, Indeed, and Glassdoor by keyword and location. New jobs are stored and deduped automatically.
2. **Job Scoring** – Each job is scored 0–100 against your keyword list, exclude-list, location preferences, and remote preference. Configurable threshold (default 70) gates document generation.
3. **Resume & Cover Letter Tailoring** – For high-scoring jobs, the app calls OpenAI to produce a tailored resume and cover letter based on the job description and your stored base resume.
4. **Notification** – When high-scoring jobs are found, an email notification is sent to your configured address with a link to the ready documents.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.10+), SQLModel, PostgreSQL |
| Scraping | Playwright + BeautifulSoup4 |
| AI Tailoring | LiteLLM (OpenAI, Anthropic, Gemini, Ollama) |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| UI Components | shadcn/ui (Radix primitives + Tailwind) |
| Frontend State | TanStack Query |
| Dev Tooling | uv, Ruff, mypy, ty, Biome |
| Local Dev | Docker Compose |
| Production | Docker images + k3s (Kubernetes) |

## Architecture

```
┌─────────────────────────────────────────────┐
│  Browser                                     │
│  React SPA  (port 5173 dev / nginx prod)    │
└──────────────────┬──────────────────────────┘
                   │  HTTP /api/v1
┌──────────────────▼──────────────────────────┐
│  FastAPI Backend  (port 8000)               │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ /jobs    │ │ /profile │ │ /documents  │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
│  ┌─────────────────────────────────────────┐│
│  │  Services: scraper · scorer · tailor   ││
│  └─────────────────────────────────────────┘│
└──────────────┬──────────────────┬───────────┘
               │                  │
      ┌────────▼──────┐  ┌────────▼───────┐
      │  PostgreSQL   │  │  OpenAI API    │
      └───────────────┘  └────────────────┘
```

The frontend proxies all `/api` calls to the backend in both dev (Vite proxy) and production (nginx proxy_pass). There is no direct database access from the frontend.

## UI Design

### Visual Design
- **Theme**: Dark mode default — `zinc-950`/`zinc-900` backgrounds, `zinc-800` cards, `zinc-700` borders
- **Accent color**: `emerald-400` — signals match quality (green = good fit)
- **Score badges**: emerald (≥70) / yellow (40–69) / red (<40)
- **Primary action**: Apply button is bold and prominent — the core user action

### Layout
```
┌──────────┬──────────────────────────────┬──────────────────┐
│          │                              │                  │
│ Sidebar  │       Main Content           │  Notifications   │
│  Nav     │                              │  Panel           │
│          │  (Dashboard / Jobs /         │  (dashboard only)│
│          │   Profile / Documents)       │                  │
└──────────┴──────────────────────────────┴──────────────────┘
```
- **Left sidebar**: persistent nav — Dashboard, Jobs, Profile, Documents
- **Right notifications panel**: visible on Dashboard only; collapses away on other pages
- **Jobs detail**: slide-out `Sheet` from the right — no page navigation needed

### Pages

#### Dashboard
- 4 stat cards: Total Jobs / High Score Jobs / Applied / Docs Generated
- **Notifications panel** (right): jobs scoring ≥ threshold, each card shows title, company, score badge, **View Docs** button (opens slide-out), **Apply →** link to job URL
- Last scrape time + **Scrape Now** button

#### Jobs
- Full-width filterable table; status tabs: All / New / High Score / Applied / Rejected
- Columns: Title, Company, Location, Score badge, Status, Date scraped
- Click any row → **slide-out detail panel** containing:
  - **Job** tab: full description + metadata
  - **Resume** tab: AI-generated resume (Markdown rendered)
  - **Cover Letter** tab: AI-generated cover letter (Markdown rendered)
  - **Apply →** button (opens job URL in new tab) — pinned at bottom of slide-out
  - **Generate Docs** button if documents don't exist yet
  - **Regenerate** button if documents already exist

#### Profile
- Resume text: large textarea
- Skills: tag input (type + Enter to add, click × to remove)
- Scoring keywords: tag input for include list; separate tag input for exclude list
- Location preference: text input
- Remote preference: toggle
- Notification email: text input
- Score threshold: number input (default 70)

#### Documents
- Card grid of all generated documents
- Filter by job (dropdown) and type (resume / cover letter)
- Each card: job title, doc type badge, date generated, **Preview** button (opens Markdown in a modal)

## Data Model

- **jobs** – scraped listings: title, company, location, url (unique), description, score, source, status (new/scored/applied/rejected)
- **user_profiles** – single-user config: base resume text, skills, scoring criteria (JSON), notification email
- **documents** – AI-generated output: linked to a job, type (resume/cover_letter), content text

## Development Phases

### Phase 1 – Infrastructure & Scaffold
- [x] Project structure (backend, frontend, k8s)
- [x] Docker Compose for local dev
- [x] k3s manifests skeleton
- [x] FastAPI routes + SQLModel models (jobs, profile, documents)
- [x] JWT auth (login / refresh / logout)
- [x] Bruno API test collection
- [x] Frontend scaffold: Vite + React 18 + TypeScript + Tailwind + shadcn/ui
- [x] Frontend pages: Dashboard, Jobs, Profile, Documents (shells)
- [x] Vite proxy `/api` → `http://localhost:8000`
- [x] Backend tests: pytest + pytest-asyncio + SQLite (auth, jobs, profile, documents)
- [x] Frontend tests: Vitest + React Testing Library (Button, Login, ProtectedRoute)
- [x] E2E: Playwright config + auth spec
- [ ] Auto-generated API client from OpenAPI schema (`scripts/generate-client.sh`)

### Phase 2 – Core Backend
- [x] Alembic migration setup (replaces `create_all` on startup)
- [x] Pre-commit hooks: trailing whitespace, YAML/TOML, Ruff, mypy, ty, Biome, SDK generation
- [ ] Scraper implementation (Indeed/LinkedIn using Playwright)
- [ ] Full scoring engine: keyword match, location match, salary extraction
- [ ] Profile CRUD with validation

### Phase 3 – AI Integration
- [ ] Multi-provider AI layer via **LiteLLM** in `services/tailor.py`
  - Supported providers: OpenAI, Anthropic (Claude), Google (Gemini), Ollama (local or remote)
  - Provider + model selected entirely via `AI_MODEL` and `AI_BASE_URL` env vars — no code changes to switch
  - Ollama available two ways: Docker Compose profile (`--profile ollama`) or external host via `AI_BASE_URL`
- [ ] Resume tailoring prompt engineering
- [ ] Cover letter generation
- [ ] Document generation triggered both automatically (on high score after scrape) and manually (user-initiated from UI)
- [ ] Documents stored as Markdown text in the `documents` table
- [ ] Document download endpoint (PDF export — stretch goal)

### Phase 4 – Notifications & Automation
- [ ] SMTP email notification on high-score job discovered
- [ ] Scheduled auto-scraping (APScheduler background job)
- [ ] Frontend: job filters, document preview, status updates

### Phase 5 – Production Hardening
- [ ] k3s cluster setup on target host
- [ ] CI/CD: build and push Docker images, apply manifests
- [ ] TLS via cert-manager + Let's Encrypt
- [ ] Basic health monitoring

## Score Threshold

Default threshold for triggering document generation and notifications is **70/100**. This will be made configurable per user profile in Phase 4. Scores are computed as:
- Keyword matches contribute up to 60 points (proportional to % matched)
- Excluded keywords immediately zero the score
- Location/remote match contributes up to 40 points (Phase 2)

## Environment Variables

See `.env.example`. Key variables:
- `DATABASE_URL` – PostgreSQL DSN
- `SECRET_KEY` – FastAPI signing key
- `AI_MODEL` – LiteLLM model string (e.g. `gpt-4o-mini`, `claude-sonnet-4-6`, `gemini/gemini-2.0-flash`, `ollama/llama3.2`)
- `AI_BASE_URL` – Optional. Set to Ollama host URL when using a local or remote Ollama instance (e.g. `http://localhost:11434`). Leave blank for cloud providers.
- `OPENAI_API_KEY` – Required when `AI_MODEL` is an OpenAI model
- `ANTHROPIC_API_KEY` – Required when `AI_MODEL` is a Claude model
- `GEMINI_API_KEY` – Required when `AI_MODEL` is a Gemini model
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` – Required for Phase 4 notifications

## AI Provider Quick Reference

| Provider | `AI_MODEL` example | `AI_BASE_URL` | API key var |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | _(blank)_ | `OPENAI_API_KEY` |
| Anthropic | `claude-sonnet-4-6` | _(blank)_ | `ANTHROPIC_API_KEY` |
| Google | `gemini/gemini-2.0-flash` | _(blank)_ | `GEMINI_API_KEY` |
| Ollama (Docker) | `ollama/llama3.2` | `http://ollama:11434` | _(none)_ |
| Ollama (local host) | `ollama/llama3.2` | `http://localhost:11434` | _(none)_ |
| Ollama (remote host) | `ollama/llama3.2` | `http://192.168.1.x:11434` | _(none)_ |

## Notes

- Single-user design: JWT auth in place. Add multi-user support in Phase 5 if needed.
- Playwright requires browser binaries. The backend Dockerfile runs `playwright install --with-deps chromium` to include them.
- k3s secrets are managed via `k8s/secrets.example.yaml` — never commit the actual `secrets.yaml`.
- Ollama GPU passthrough in Docker requires the NVIDIA Container Toolkit on the host (`nvidia-docker`).
