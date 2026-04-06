# API Reference

Base URL is your backend origin (for example `https://bot.example.com`).

## Authentication model

1. Mini App sends Telegram `init_data` to `POST /api/auth/telegram`.
2. Backend validates payload and sets HttpOnly session cookie.
3. Authenticated endpoints require that session cookie.

Unauthenticated access to protected routes returns HTTP `401`.

## Health and infrastructure endpoints

### `GET /`

Service status response.

### `GET /healthz`

Simple health check response:

- `200` with `{ "ok": true }`.

### `POST /webhook/{secret}`

Telegram webhook endpoint.

- `404` if path secret does not match `WEBHOOK_PATH_SECRET`.
- `401` if `TELEGRAM_WEBHOOK_SECRET` is configured and header mismatch occurs.
- `200` with `{ "ok": true }` for accepted updates.

### Static mounts

- `GET /uploads/...` serves uploaded cat photos.
- `GET /miniapp/...` serves static SPA build (path configurable by `MINIAPP_PATH`).

## Debug endpoints

### `POST /api/__debug/client-log`

Writes JSON events to NDJSON file if `CLIENT_DEBUG_LOG_PATH` is configured.

- `404` when debug logging is disabled.
- `400` for invalid JSON payload.
- `200` with `{ "ok": "1" }` when logged.

## Auth endpoints

### `POST /api/auth/telegram`

Authenticate user from Telegram WebApp `init_data`.

Request body:

- `init_data` (string, required).

Response:

- `200` with user payload.
- Sets session cookie.

Errors:

- `401` when `init_data` validation fails.

### `POST /api/auth/logout`

Clears session cookie.

Response:

- `200` with `{ "message": "ok" }`.

## User endpoints

### `GET /api/me`

Returns current authenticated user.

### `PATCH /api/me/locale`

Updates user locale.

### `PATCH /api/me/daily-reminder-time`

Updates user preferred daily reminder time.

## Cat endpoints

### `GET /api/cats`

List current user's cats (newest first).

### `POST /api/cats`

Create a new cat.

### `PATCH /api/cats/{cat_id}`

Update cat fields (name, weight, notes, organization).

### `DELETE /api/cats/{cat_id}`

Delete cat and associated upload directory.

Returns `204` on success.

### `POST /api/cats/{cat_id}/photo`

Upload cat photo as multipart file.

Validation:

- Content type must be supported image type.
- File size must be within `MAX_UPLOAD_BYTES`.

### `DELETE /api/cats/{cat_id}/photo`

Removes photo files and clears `photo_url`.

## Scenario endpoints

### `GET /api/cats/{cat_id}/scenarios`

List scenario runs for cat (newest first).

### `POST /api/cats/{cat_id}/scenarios`

Start a scenario run.

Request body:

- `scenario_type` (required).
- `anchor_at` (optional datetime).
- `context` (optional object, scenario-specific).

Behavior:

- Cancels active runs of the same type for the cat.
- Creates run + schedules reminders.

### `POST /api/cats/{cat_id}/scenarios/{run_id}/cancel`

Cancels scenario run and marks unsent reminders as cancelled.

## Reminder endpoints

### `GET /api/cats/{cat_id}/reminders`

List all reminders for one cat ordered by `run_at`.

### `GET /api/reminders/upcoming`

List unsent + non-cancelled reminders across all user's cats.

## Dosage endpoints

### `GET /api/dosage/drugs`

Returns supported drug slugs.

### `POST /api/dosage/calculate`

Calculates drug dosage by weight.

Request body:

- `drug_slug`.
- `weight_kg`.
- `use` (`min`, `mid`, `max`; default `mid`).

Errors:

- `404` for unknown drug.
- `400` for invalid weight or input domain errors.

## Template endpoints

All template endpoints are authenticated and locale-aware.

### `GET /api/templates/sterilization_clinic`
### `GET /api/templates/potential_adopter_questions`
### `GET /api/templates/post_structure`

Each returns:

- `{ "text": "...localized template..." }`.

## Common error patterns

- `401 not_authenticated`: missing session cookie.
- `401 bad_token`: invalid/expired cookie payload.
- `401 user_missing`: user no longer exists.
- `404 not_found`: resource not owned or missing.
- `400 ...`: validation/domain failure (details vary by endpoint).
