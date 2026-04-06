# Operations and Deployment

This guide covers container runtime behavior, deployment workflow, and production operations.

## Runtime topology

Default `docker-compose.yml` runs:

- `postgres` (`postgres:16-alpine`) with persistent `pgdata` volume.
- `app` (built from root `Dockerfile`) exposing `8000:8000`.

App container includes:

- FastAPI backend.
- aiogram webhook processing.
- Reminder dispatcher loop inside same process.
- Built Mini App static assets under `/miniapp`.

## Container startup sequence

Entrypoint (`docker/entrypoint.sh`):

1. `alembic upgrade head`
2. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

Implications:

- App startup is migration-gated.
- Startup requires DB availability.
- Startup also requires valid Telegram credentials due to bot command registration.

## Environment variables (production)

Set in `.env` consumed by compose `env_file`:

Required:

- `BOT_TOKEN`
- `WEBHOOK_PATH_SECRET`
- `PUBLIC_BASE_URL`
- `DATABASE_URL`
- `SESSION_SECRET`
- `CORS_ORIGINS`

Strongly recommended:

- `TELEGRAM_WEBHOOK_SECRET`
- `SECURE_COOKIES=true`
- `SET_WEBHOOK_ON_STARTUP=false` (prefer explicit webhook management)
- `UPLOAD_ROOT` (if customizing volume path)

Optional:

- `MINIAPP_PATH`
- `MAX_UPLOAD_BYTES`
- `CLIENT_DEBUG_LOG_PATH`

## Build and run in Docker

From repo root:

```bash
docker compose up --build -d
```

Inspect status:

```bash
docker compose ps
docker compose logs --tail=200 app
```

## Webhook setup

After TLS and DNS are ready, set Telegram webhook:

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -d "url=$PUBLIC_BASE_URL/webhook/$WEBHOOK_PATH_SECRET" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

If you manage webhook manually, keep `SET_WEBHOOK_ON_STARTUP=false`.

## Reverse proxy and TLS

You must terminate TLS before Telegram traffic reaches app.

Example Caddy reverse proxy:

```text
bot.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Operational checks:

- `https://<host>/healthz` returns `{ "ok": true }`.
- `https://<host>/miniapp/` serves SPA.
- Session cookies have `Secure` + `SameSite=None` in HTTPS deployments.

## GitHub Actions workflows

### CI (`.github/workflows/ci.yml`)

Triggers:

- push
- pull_request
- workflow_dispatch

Jobs:

- backend: install deps, ruff, pytest.
- docker: build image.

### Deploy (`.github/workflows/deploy.yml`)

Trigger:

- workflow_dispatch only.

Behavior:

- SSH into server.
- `cd $VPS_DEPLOY_PATH`
- `git pull`
- `docker compose build --pull`
- `docker compose up -d`

Required repository secrets:

- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `VPS_DEPLOY_PATH`

## Monitoring and diagnostics

Useful checks:

```bash
curl -fsS https://<host>/healthz
docker compose logs --tail=200 app
docker compose logs --tail=200 postgres
```

If enabled, client debug events are written to `CLIENT_DEBUG_LOG_PATH` as NDJSON.

## Backup and persistence

Data with persistence requirements:

- Postgres volume (`pgdata`).
- Uploads volume (`cat_uploads` mapped to `/app/data/uploads`).

Minimum backup strategy:

- Scheduled Postgres dumps.
- Periodic uploads directory backup.
- Retention policy with restore drills.

## Scaling notes

Current architecture keeps reminder loop in application process.

Consequences:

- Horizontal scaling without coordination may duplicate reminder dispatch.
- Single instance is appropriate for small deployments.

For multi-instance scaling, split dispatcher into dedicated worker with distributed locking.

## Incident playbook (quick reference)

### App won’t start

Check in order:

1. Postgres is healthy and reachable.
2. `DATABASE_URL` uses async driver and correct host.
3. Migrations apply cleanly.
4. `BOT_TOKEN` is valid.

### Webhook events not processed

Check in order:

1. DNS and TLS for `PUBLIC_BASE_URL`.
2. Webhook URL and secret values.
3. `POST /webhook/{secret}` not blocked by proxy/firewall.
4. App logs for auth/parse errors.

### Mini App auth failures

Check in order:

1. Cookie flags (`SECURE_COOKIES`, HTTPS).
2. `CORS_ORIGINS` includes expected origins.
3. Backend clock/time sync and token verification path.

### Upload failures

Check in order:

1. Proxy body-size limits.
2. `MAX_UPLOAD_BYTES`.
3. Upload volume permissions and free disk space.
