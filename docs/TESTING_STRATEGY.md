# Testing strategy

Tests cover the path a reviewer will ask about. They do not try to exhaust the UI.

## Backend

`backend/tests` uses a temporary SQLite file. `conftest.py` points `DATABASE_URL` at that file and runs `alembic upgrade head`, then asserts the eight tables exist.

Covered:

- Signup, login, wrong password, and unauthenticated profile access.
- Profile save.
- A fakeredis RQ worker that persists an assessment and roadmap.
- A second user receives 404 for the first user's job and task.
- Gap math, including the `postgres` → SQL alias, and the "not a verified score" wording.
- Narrative schema bounds and ignored injection fields.
- Demo resources are `https` links and say they are not live search.

External AI and search clients are not called. Empty keys force demo mode.

## Frontend

Vitest checks the completion helper and the labels that avoid calling a self-report "verified". `npm run build` typechecks the App Router pages.

## Not in CI

Playwright, live OpenAI, and live Tavily. A manual smoke test is: sign up, save a profile, run the worker, open the roadmap, mark a task complete, refresh the dashboard.
