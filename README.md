# Batumi Curator

Batumi Curator is a Telegram Mini App + bot backend for street-animal curator workflows: cat records, scenario-driven reminders, helper templates, and medication dosage lookup.

## What this repository contains

- `backend/` — FastAPI API, Telegram webhook handling, reminder dispatcher, Alembic migrations.
- `miniapp/` — Vite + React + TypeScript Telegram Mini App.
- `docker-compose.yml` — Postgres + app composition for container runtime.
- `Dockerfile` — multi-stage image that bundles backend and Mini App static build.

## Documentation index

- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Local Development Guide](docs/local-development.md)
- [Operations and Deployment](docs/operations-and-deployment.md)

## Quick start (local)

### 1) Start Postgres

```bash
sudo docker compose up -d postgres
POSTGRES_IP=$(sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' workspace-postgres-1)
```

### 2) Configure backend env

```bash
cp .env.example backend/.env
```

Set required values in `backend/.env`:

- `BOT_TOKEN`
- `WEBHOOK_PATH_SECRET`
- `PUBLIC_BASE_URL`
- `DATABASE_URL=postgresql+asyncpg://curator:curator@<POSTGRES_IP>:5432/curator`
- `SESSION_SECRET`
- `SECURE_COOKIES=false` (for local HTTP)
- `CORS_ORIGINS=http://localhost:5173,https://web.telegram.org`
- `SET_WEBHOOK_ON_STARTUP=false`

### 3) Install backend deps + migrate + run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Run miniapp

```bash
cd miniapp
npm install
npm run dev
```

Mini App dev server runs on `http://localhost:5173` and proxies `/api` to backend.

## Development commands

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

## Docker run

Create `.env` in repository root (based on `.env.example`) and run:

```bash
docker compose up --build
```

## Telegram setup (production)

1. Create a bot via [@BotFather](https://t.me/BotFather).
2. Set Mini App URL to `https://<host>/miniapp/` (or your configured `MINIAPP_PATH`).
3. Configure webhook after HTTPS is active:

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -d "url=$PUBLIC_BASE_URL/webhook/$WEBHOOK_PATH_SECRET" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

## CI/CD

- CI workflow (`.github/workflows/ci.yml`) runs Ruff, pytest, and Docker build.
- Deploy workflow (`.github/workflows/deploy.yml`) performs manual SSH deployment to VPS.

## Known caveats

- Backend startup requires a valid `BOT_TOKEN` because bot commands are registered in startup lifespan.
- Migrations must be applied before serving requests.
- For Telegram WebApp cookie behavior, production should use HTTPS with `SECURE_COOKIES=true`.
