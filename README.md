# Batumi curator Telegram Mini App

FastAPI + PostgreSQL + aiogram bot with a React Mini App for cat/dog curator workflows: per-cat scenarios, scheduled reminders (RU/EN/KA), templates, and a simple mg/kg dosage helper.

## Repository layout

- `backend/` — API, bot webhook, reminder worker loop, Alembic migrations, JSON locales
- `miniapp/` — Vite + React Telegram Mini App (build output copied into the image)
- `docker-compose.yml` — Postgres + app

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export BOT_TOKEN="123:abc"
export WEBHOOK_PATH_SECRET="dev-secret"
export PUBLIC_BASE_URL="https://example.com"
export DATABASE_URL="postgresql+asyncpg://curator:curator@localhost:5432/curator"
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export SECURE_COOKIES=false
export CORS_ORIGINS="http://localhost:5173,https://web.telegram.org"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Mini App

```bash
cd miniapp
npm install
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`. After changing the UI, build static files for the backend container or local serving:

```bash
cd miniapp
npm run build
mkdir -p ../backend/app/static/miniapp
rm -rf ../backend/app/static/miniapp/*
cp -r dist/* ../backend/app/static/miniapp/
```

## Docker Compose (Postgres + app)

Copy `.env.example` to `.env` and set real values. Compose overrides `DATABASE_URL` for the `app` service.

```bash
docker compose up --build
```

## Telegram setup

1. Create a bot with [@BotFather](https://t.me/BotFather), obtain `BOT_TOKEN`.
2. Set the Mini App URL to your public HTTPS URL including the path, e.g. `https://bot.example.com/miniapp/` (must match `PUBLIC_BASE_URL` + `MINIAPP_PATH`).
3. Set the webhook after TLS is working:

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -d "url=$PUBLIC_BASE_URL/webhook/$WEBHOOK_PATH_SECRET" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

Optional: set `SET_WEBHOOK_ON_STARTUP=true` in `.env` so the app calls `setWebhook` on boot.

4. For local debugging, use a tunnel (e.g. ngrok) with HTTPS and point BotFather + `PUBLIC_BASE_URL` to that host.

## VPS + TLS (Caddy example)

Point an `A` record at the server. Example `Caddyfile`:

```text
bot.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Run `docker compose` (or the stack you prefer) on the host and let Caddy obtain Let’s Encrypt certificates.

## CI/CD

- `.github/workflows/ci.yml` — Ruff, pytest, and `docker build` on **every push** (any branch) and on **every pull request**. Manual runs: **Actions** → **CI** → **Run workflow**.
- If the **Actions** tab shows no runs, open **Settings → Actions → General** and allow GitHub Actions for this repository (and for forks, the policy you need).
- `.github/workflows/deploy.yml` — manual **Run workflow**; requires secrets `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_DEPLOY_PATH` (absolute path to this repo on the server with your `.env` and `docker-compose.yml`).

## Notes

- Session cookies for the Mini App use `SameSite=None` when `SECURE_COOKIES=true` (required for Telegram WebApp + HTTPS).
- Reminders are stored in Postgres and dispatched by a background loop inside the Uvicorn process (fine for ~100 users on a single instance).
