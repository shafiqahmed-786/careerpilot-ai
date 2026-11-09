# CareerPilot AI — agent notes

Work in this repository. Do not recreate the frontend or backend.

- API code lives in `backend/app`. Routes are in `backend/app/api.py` under `/api/v1`.
- The assessment path is `POST /assessments` → PostgreSQL job → Redis/RQ → `python -m app.worker` → `app.pipeline.run_and_persist`.
- Scores are computed in `app/gaps.py` and never by an LLM. The LLM writes prose: assessment narrative (`app/ai.py`), the roadmap plan (`app/roadmap_ai.py`, validated, labelled fallback in `roadmap_builder.py`), resume analysis (`app/resume_analysis.py`, every skill verified by `app/evidence.py`) and mentor replies (`app/mentor.py`). URLs come only from `app/search.py` (Tavily or the demo catalog).
- One queue serves three job kinds (`assessment`, `adapt`, `resume`); all LLM calls go through `app/llm.py`. Never log resume text or prompts.
- Demo mode is the default when `GROQ_API_KEY` or `TAVILY_API_KEY` is empty. Keep the `demo` label.
- Authorize with the JWT subject. Filter every read and write by `user_id`.
- On Windows, run the queue with `WindowsWorker` from `app/queue.py`.
- Frontend routes live only in `frontend/src/app` (no root `app/` directory). Shared code is imported with `@/*` (maps to `src/*`).
- Tests: `cd backend` then `python -m pytest -q`. Frontend: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
- Do not commit `.env`. Do not claim a deployment that has not been verified.
