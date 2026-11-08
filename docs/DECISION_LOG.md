# Decision log

| Decision | Reason |
| --- | --- |
| New standalone project | The brief requires a new project, not an extension of RuFlow or MedResearch. |
| FastAPI + PostgreSQL + Alembic | Typed API, relational ownership, versioned schema. |
| JWT and bcrypt instead of a hosted auth provider | No external account is needed to run or review the MVP. Tokens expire; passwords are hashed. |
| Reject passwords over 72 UTF-8 bytes | bcrypt ignores everything past 72 bytes (and newer versions raise). Rejecting is honest; silent truncation is not. |
| Validate email with `email-validator`, store lower-case | Prevents case-variant duplicates. Syntax only, no DNS lookup, so it works offline and in CI. |
| Unique index is the source of truth for duplicates | A pre-check is not race-safe. An `IntegrityError` is caught, rolled back, and returned as `409`. |
| Scores in code, prose in the model | A rubric can be tested. A model must not be the source of a priority score or a URL. |
| Tavily or a labelled demo catalog | Live search by default when configured; development and CI work with no key. |
| No RAG / vector database | There is no private corpus. Public learning links are a search problem. |
| Redis + RQ, separate worker | Keeps slow external calls out of requests; one queue is enough. |
| `SimpleWorker` on Windows | Windows cannot `fork` or arm `SIGALRM`; the worker is still a separate process. |
| 500 handler inside CORS middleware | Otherwise an unhandled error has no CORS headers and the browser reports "Failed to fetch", hiding the cause. |
| Any localhost port allowed in non-production CORS | Browsers treat `localhost`, `127.0.0.1`, and each port as different origins; a mismatch looked like a signup failure. |
| One App Router tree: `frontend/src/app` | A root `app/` directory takes precedence over `src/app/`; duplicate trees silently shadow each other. `@/*` already maps to `src/*`. |
| Dashboard returns `latest_job` | Polling survives page refreshes (no reliance on `sessionStorage`) and shows failures with a retry. |
| Compose profiles | `docker compose up -d` starts only PostgreSQL and Redis; API and worker containers are opt-in (`--profile app`). |
| SQLite in pytest, PostgreSQL elsewhere | Tests need no database service; the migration uses portable types. |
| String UUID primary keys | Same ids on SQLite and PostgreSQL. |
| No push, no deployment from the build environment | The owner creates the GitHub repository and deploys. |

## v2 decisions

| Decision | Reason |
| --- | --- |
| Mentor replies inside the request, not the queue | Chat must feel responsive; a 40 s timeout and a labelled fallback bound the wait |
| Roadmap, adaptation and resume analysis through RQ | Slow, retryable operations; reuses the existing worker and job table via `kind` |
| No streaming | Simpler and testable; typing indicator covers the wait |
| `pypdf` + stdlib `zipfile`, no DOCX library | Smallest dependency set; DOCX text read with regexes avoids XML-bomb parsing |
| Upload parsed in memory, text kept until analysis ends | Raw files are never stored; text is cleared after the worker finishes |
| Evidence quotes verified against the resume | A model must not be able to assert evidence that is not there |
| Resume match is a formula, labelled "evidence coverage" | Reproducible number; no LLM percentage |
| Adapt deletes only `pending` tasks | Preserves completed history and in-progress work |
| Dark design system in Tailwind, no component library | Requested visual direction without new dependencies |
| `(app)` route group with one `AppShell` | Single auth gate, sidebar and transitions for all authenticated pages |
