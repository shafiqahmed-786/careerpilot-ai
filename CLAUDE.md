# CareerPilot AI — agent notes

Work in this repository. Do not recreate the frontend or backend.

- API code lives in `backend/app`. Routes are in `backend/app/api.py` under `/api/v1`.
- The assessment path is `POST /assessments` → PostgreSQL job → Redis/RQ → `python -m app.worker` → `app.pipeline.run_and_persist`.
- Scores are computed in `app/gaps.py`. The LLM may rewrite only the summary. URLs come from `app/search.py`.
- Demo mode is the default when `OPENAI_API_KEY` or `TAVILY_API_KEY` is empty. Keep the `demo` label.
- Authorize with the JWT subject. Filter every read and write by `user_id`.
- On Windows, run the queue with `WindowsWorker` from `app/queue.py`.
- Frontend routes live only in `frontend/src/app` (no root `app/` directory). Shared code is imported with `@/*` (maps to `src/*`).
- Tests: `cd backend` then `python -m pytest -q`. Frontend: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
- Do not commit `.env`. Do not claim a deployment that has not been verified.
