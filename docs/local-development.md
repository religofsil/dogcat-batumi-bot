# Local Development Guide

This guide describes how to run Batumi Curator in a local development environment.

## Prerequisites

- Python 3.12
- Node.js 22+
- npm
- Docker + Docker Compose

## Project structure

- `backend/`: FastAPI API + bot webhook + reminder loop + migrations.
- `miniapp/`: Vite React Telegram Mini App.
- `docker-compose.yml`: local Postgres service.

## 1) Start PostgreSQL

From repository root:

```bash
sudo docker compose up -d postgres
```

Get container IP (required because compose service does not publish DB port to host by default):

```bash
POSTGRES_IP=$(sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' workspace-postgres-1)
echo "$POSTGRES_IP"
```

## 2) Configure backend environment

Copy env template:

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and set at minimum:

- `BOT_TOKEN` (must be valid for full backend startup).
- `WEBHOOK_PATH_SECRET`.
- `PUBLIC_BASE_URL`.
- `DATABASE_URL=postgresql+asyncpg://curator:curator@<POSTGRES_IP>:5432/curator`.
- `SESSION_SECRET`.
- `SECURE_COOKIES=false` for local HTTP.
- `CORS_ORIGINS=http://localhost:5173,https://web.telegram.org`.
- `SET_WEBHOOK_ON_STARTUP=false` for local dev.

## 3) Install backend dependencies and run migrations

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
```

## 4) Run backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Notes:

- Backend startup calls Telegram API to register commands; dummy token causes startup failure.
- For API-only local testing without real token, prefer `pytest` or ASGI transport tests.

## 5) Run miniapp

```bash
cd miniapp
npm install
npm run dev
```

Vite starts on `http://localhost:5173` and proxies `/api` to `http://127.0.0.1:8000`.

## Useful development commands

### Backend lint

```bash
cd backend
source .venv/bin/activate
ruff check app tests
```

### Backend tests

```bash
cd backend
source .venv/bin/activate
pytest
```

### Miniapp build

```bash
cd miniapp
npm run build
```

### Serve built miniapp from backend (manual local copy)

```bash
cd miniapp
npm run build
mkdir -p ../backend/app/static/miniapp
rm -rf ../backend/app/static/miniapp/*
cp -r dist/* ../backend/app/static/miniapp/
```

## Telegram testing notes

- Mini App requires HTTPS in real Telegram clients.
- For local bot/webhook testing, use an HTTPS tunnel and set:
  - Bot Mini App URL: `<PUBLIC_BASE_URL><MINIAPP_PATH>/`
  - Webhook URL: `<PUBLIC_BASE_URL>/webhook/<WEBHOOK_PATH_SECRET>`

## Common issues

### `TelegramUnauthorizedError` on backend startup

Cause: invalid `BOT_TOKEN`.

Fix: use a real bot token or test with pytest path that mocks startup dependencies.

### Database connection errors on startup

Cause: Postgres not running, wrong container IP, or wrong async DB URL.

Fix:

- Ensure `postgres` service is healthy.
- Re-check container IP.
- Ensure URL uses `postgresql+asyncpg://...`.

### Alembic migration errors

Cause: stale DB state or incorrect DB URL.

Fix:

- Re-run `alembic upgrade head` with activated venv and correct env vars.
- Verify `DATABASE_URL` in `backend/.env`.

### Photo upload `413` behind reverse proxy

Cause: proxy body size limit.

Fix: raise proxy size limit (e.g., nginx `client_max_body_size`) and align with backend `MAX_UPLOAD_BYTES`.
