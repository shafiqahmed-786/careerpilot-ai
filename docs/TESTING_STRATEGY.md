# Testing strategy

Goal: a reliable MVP, not a large framework. External services are never required.

## Backend (pytest, `cd backend && python -m pytest -q`)

- Settings: temporary SQLite database, `alembic upgrade head` is executed once per session and the expected tables are asserted. OpenAI and Tavily keys are empty, so the demo paths run.
- `test_auth.py`: signup/login, email normalization, duplicate and simulated concurrent duplicate (`409`), invalid emails, short/blank/over-72-byte passwords, byte-limit boundary, unknown user, invalid and expired tokens, hashing helpers, readiness (database + migrations), CORS for another localhost port.
- `test_api.py`: health, `me`, profile + protected route, and the full journey with fakeredis: create job → worker (`SimpleWorker`, burst) → job `completed` → assessment, resources (all `demo`, all `https`), roadmap → ownership checks (`404` for another user) → task update → dashboard reflects it, including `latest_job`.
- `test_gaps.py`, `test_schemas.py`, `test_search.py`: rubric arithmetic and statuses, narrative schema drops extra fields, demo resources.
- `scripts/smoke_journey.py`: the same journey against your real Postgres and Redis (`scripts/verify.ps1` / `verify.sh`).

Lint: `ruff check app tests`.

## Frontend (`cd frontend`)

- `npm run lint`, `npm run typecheck`, `npm test` (Vitest: progress helpers, API error formatting, form validation), `npm run build`.

## Manual end-to-end check

Run `scripts/dev.ps1`, sign up with a new email, save a profile, watch the dashboard move from queued to completed, open the roadmap, complete a task, add a note, refresh, and confirm the dashboard percentage. Stop the worker and confirm the "worker not running" hint appears for a queued job. Stop Redis and confirm the `503` message.

## Not covered (known)

Browser-level tests, load tests, and live OpenAI/Tavily calls (they need keys and cost money).

## CI

GitHub Actions runs backend lint + tests, frontend lint + typecheck + tests + build, and `docker compose --profile app config --quiet`.
