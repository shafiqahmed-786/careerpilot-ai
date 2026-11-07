# Implementation plan

Status reflects the repository contents. Items marked "owner" need your accounts.

| Phase | Work | Status |
| --- | --- | --- |
| 1. Foundation | Repo layout, FastAPI app, SQLAlchemy models, Alembic `0001_initial`, Docker Compose for PostgreSQL and Redis | Done |
| 2. Authentication | Signup/login, bcrypt, JWT, protected routes, owner-scoped queries | Done |
| 3. Profile and queue | Profile API, job table, Redis/RQ enqueue, separate worker | Done |
| 4. Assessment pipeline | Gap rubric, role catalog, Tavily + demo catalog, OpenAI + template narrative, roadmap builder | Done |
| 5. Frontend journey | Landing, signup, login, onboarding, dashboard, roadmap | Done |
| 6. Stabilization | Email/password validation (72-byte rule), race-safe duplicate signup, API error handling, CORS and 500 handling, single App Router tree, dashboard job polling and retry, notes saving, readiness migrations check | Done |
| 7. Tests and CI | Pytest, Vitest, GitHub Actions (backend, frontend, compose config) | Done; run locally to confirm on your machine |
| 8. Local tooling | `scripts/setup`, `dev`, `verify` for PowerShell and Bash, smoke journey | Done |
| 9. Publish | Create the public GitHub repo and push | Owner |
| 10. Deploy | Vercel + Render + managed Postgres/Redis, then set the live URL in the README | Owner |

## Next after the MVP

Email verification and password reset, refresh tokens or httpOnly cookies, more role rubrics, re-generating a roadmap while keeping completed tasks, RAG only if a private corpus (notes, syllabus) is added.
