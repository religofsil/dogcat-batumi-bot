# Architecture

This project is a Telegram-first curator workflow system with a FastAPI backend and a React Mini App.

## High-level design

- `backend/` hosts:
  - HTTP API (`/api/...`) for the Mini App.
  - Telegram webhook endpoint (`/webhook/{secret}`) for bot updates.
  - Background reminder dispatcher loop started in app lifespan.
  - Database migrations (Alembic).
- `miniapp/` hosts:
  - Telegram Mini App SPA (Vite + React + TypeScript).
  - API client that talks to backend endpoints.
- Docker build combines both:
  - Builds miniapp static files.
  - Copies them into backend static directory.
  - Runs one container serving API + static Mini App.

## Runtime components

### Backend app

Main entrypoint: `backend/app/main.py`.

Responsibilities:

- Loads settings from env.
- Starts aiogram bot + dispatcher.
- Registers bot commands on startup.
- Optionally sets Telegram webhook on startup.
- Starts reminder worker loop (`reminder_loop`) in background.
- Mounts API routers.
- Serves uploads from `/uploads`.
- Serves Mini App static files from `MINIAPP_PATH` (default `/miniapp`) when built assets exist.

### Telegram integration

- Authentication for Mini App is done via `POST /api/auth/telegram` with Telegram `init_data`.
- Session is stored as signed cookie (HttpOnly).
- Bot updates come via `POST /webhook/{WEBHOOK_PATH_SECRET}`.
- Optional extra secret validation with `X-Telegram-Bot-Api-Secret-Token`.

### Reminder processing

- Scenario starts create scheduled reminders in DB.
- Background loop periodically checks due reminders and sends Telegram messages.
- Reminder metadata includes `run_at`, `sent_at`, cancellation state, and errors.

## Data model

Core entities:

- `User`
  - Telegram identity (`telegram_id`), locale, preferred daily reminder time.
- `Cat`
  - Belongs to user, has name/weight/notes/photo/organization.
- `ScenarioRun`
  - Scenario instance per cat, with type, status, context payload.
- `Reminder`
  - Scheduled reminder linked to cat and optionally scenario run.

Relationships:

- User `1 -> many` Cats.
- Cat `1 -> many` ScenarioRuns.
- Cat `1 -> many` Reminders.
- ScenarioRun `1 -> many` Reminders.

## Scenario engine

Scenario types:

- `new_capture`
- `adopted_home`
- `post_prep`
- `potential_adopter`
- `sterilization`

Lifecycle:

1. User starts scenario for a cat.
2. Active runs of the same type for that cat are cancelled.
3. New run is inserted with `active` status.
4. Reminders are generated according to scenario rules and user reminder time.
5. Dispatcher sends reminders when due.

## Frontend architecture

- Single-page app rooted in `miniapp/src/App.tsx`.
- No dedicated router package; view state is managed in component logic.
- Telegram WebApp APIs are used for integration context.
- i18n via `i18next` + `react-i18next`.
- Vite dev server proxies `/api` to backend in local development.

## Build and packaging

### Local development

- Backend and miniapp run as separate dev processes.
- Miniapp proxies API traffic to backend.

### Containerized runtime

`Dockerfile` is multi-stage:

1. Build miniapp (`npm run build`).
2. Build Python runtime image.
3. Install backend requirements.
4. Copy backend code and miniapp build output.
5. Start with entrypoint that applies Alembic migrations then launches uvicorn.

## CI/CD model

- CI workflow:
  - Ruff lint (backend).
  - Pytest (backend).
  - Docker image build.
- Deploy workflow (manual dispatch):
  - SSH to VPS.
  - `git pull`.
  - `docker compose build --pull`.
  - `docker compose up -d`.

## Security and trust boundaries

- Public attack surface:
  - `/api/...`
  - `/webhook/{secret}`
  - static files under `/miniapp` and `/uploads`.
- Primary controls:
  - Session cookie signing.
  - Telegram `init_data` validation.
  - Webhook path secret and optional Telegram secret header.
  - CORS allowlist.
  - Upload content-type and payload-size checks.

## Known operational caveats

- Backend startup requires valid `BOT_TOKEN` because it registers bot commands during startup.
- PostgreSQL must be reachable before app starts.
- Migrations must be current (`alembic upgrade head`).
- For Telegram WebApp in production, HTTPS and secure cookies are required.
