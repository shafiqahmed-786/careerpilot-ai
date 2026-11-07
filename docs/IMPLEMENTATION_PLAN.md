# Implementation record

The checked-in tree is the MVP. There was no existing CareerPilot checkout on this machine, so the application was built here rather than resumed from `/home/claude/careerpilot-ai`.

## Built

- JWT auth, profile CRUD, and ownership checks.
- Assessment jobs enqueued to Redis and consumed by a separate RQ worker.
- Rubric scoring, demo or Tavily resources, demo or OpenAI narrative, and a persisted roadmap.
- Dashboard and roadmap UI, including task status and notes.
- Alembic's initial migration, pytest, Ruff, GitHub Actions, Docker Compose, and Render start commands.

## Deliberately not built

Resume upload, interview prep, mentoring, notifications, and a vector store.

## Order of work

1. Schema, auth, and the job queue.
2. Scoring, search, narrative, and roadmap persistence.
3. Screens that call those endpoints.
4. Tests, lint, the production frontend build, and these docs.
