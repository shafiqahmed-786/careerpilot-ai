# Decision log

| Decision | Reason |
| --- | --- |
| New tree at `careerpilot-ai` | No CareerPilot project was present on this machine. The Linux path in the brief does not exist here. |
| JWT and bcrypt instead of Clerk | No Clerk keys or existing Clerk integration were available. Tokens expire and passwords are hashed. |
| Scores in code, prose in the model | A rubric can be tested. A model must not be the source of a priority score or a URL. |
| Tavily or a labelled demo catalog | Live search is the right default, and local development still works with no key. |
| No RAG | There is no private corpus. Public learning links are a search problem. |
| Redis + RQ, not Celery | The brief requires RQ and a separate worker. One queue is enough. |
| `SimpleWorker` on Windows | CPython on Windows cannot `fork`. RQ's Unix alarm also does not exist, so the Windows worker uses a no-op death penalty. |
| SQLite in pytest, PostgreSQL in Docker and production | CI and laptops can run tests without a database service. The migration uses portable types and is what production runs. |
| String UUID primary keys | The same ids work on SQLite and PostgreSQL. |
| CORS includes localhost and 127.0.0.1 | Browsers treat those hosts as different origins. |
| No GitHub push | The brief says the user handles repository creation, commits, and deployment accounts. |
