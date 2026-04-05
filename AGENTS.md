# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Batumi Curator is a Telegram Mini App with two services:

| Service | Stack | Dev command |
|---|---|---|
| **Backend** (API + bot webhook + reminder worker) | Python 3.12 / FastAPI / SQLAlchemy async / Alembic / aiogram | `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| **Miniapp** (frontend SPA) | Vite + React + TypeScript | `cd miniapp && npm run dev` (port 5173, proxies `/api` → backend) |
| **PostgreSQL 16** | Docker Compose | `sudo docker compose up -d postgres` |

### Important caveats

- **The backend requires a valid Telegram `BOT_TOKEN` to start.** The lifespan calls `register_bot_commands(bot)` which contacts the Telegram API. With a dummy token, uvicorn will crash with `TelegramUnauthorizedError`. To test API endpoints without a real token, use `pytest` or the httpx ASGI transport with mocked bot setup (see tests for reference pattern).
- **PostgreSQL must be running before the backend starts.** The docker-compose postgres service does not map ports to the host by default; connect using the container's IP (`sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' workspace-postgres-1`).
- **Alembic migrations** must be run before the backend can serve requests: `cd backend && alembic upgrade head`.
- **Environment variables** are documented in `.env.example`. For local dev, at minimum set: `BOT_TOKEN`, `WEBHOOK_PATH_SECRET`, `PUBLIC_BASE_URL`, `DATABASE_URL`, `SESSION_SECRET`, `SECURE_COOKIES=false`, `CORS_ORIGINS`.

### Lint / Test / Build

- **Lint (backend):** `cd backend && source .venv/bin/activate && ruff check app tests`
- **Test (backend):** `cd backend && source .venv/bin/activate && pytest` (tests set their own env vars in `conftest.py` so no DB or bot token needed)
- **Build (miniapp):** `cd miniapp && npm run build`
- **CI mirrors:** see `.github/workflows/ci.yml` — runs ruff, pytest, docker build

### Docker

- Full-stack Docker build: `docker compose up --build` (requires valid `.env` with real `BOT_TOKEN`)
- Docker is needed in the cloud VM for PostgreSQL. The daemon must be started with fuse-overlayfs storage driver and iptables-legacy.
