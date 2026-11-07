# Agent guide

CareerPilot AI is a Next.js and FastAPI product. Read `README.md` and `docs/ARCHITECTURE.md` before changing the pipeline.

Preserve:

- PostgreSQL models and the Alembic revision in `backend/alembic/versions/0001_initial.py`.
- Redis plus a separate RQ worker.
- Ownership checks on jobs, assessments, roadmaps, and tasks.
- The distinction between self-reported levels, rubric scores, live Tavily results, and the demo catalog.

Change the smallest module that fixes the behavior. Add a test next to `backend/tests` when the change affects scoring, auth, or persistence. Do not add a vector database, a second queue, or a second auth provider unless the product requirement changes.
- Backend tests: `cd backend && python -m pytest -q`. Frontend routes live only in `frontend/src/app`.
