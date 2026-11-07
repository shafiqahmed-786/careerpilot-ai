# Data model

Identifiers are UUID strings. Timestamps are timezone-aware.

| Table | Role |
| --- | --- |
| `users` | Email and password hash. |
| `profiles` | One row per user. Skills are JSON objects `{name, proficiency}`. |
| `assessment_jobs` | Queue state: `queued`, `running`, `completed`, `failed`. Holds RQ id, error, and result ids. |
| `assessments` | Normalized role, summary, learn-first reason, disclaimer, narrative provider, rubric version. |
| `competency_results` | One scored competency per assessment, owned by `user_id`. |
| `learning_resources` | Retrieved or demo links for an assessment. |
| `roadmaps` | One plan for an assessment. |
| `roadmap_tasks` | Week, objective, skills, hours, outcome, criteria, resource JSON, status, notes. Unique `(roadmap_id, sort_order)`. |

`user_id` is stored on jobs, assessments, competencies, resources, roadmaps, and tasks so a query can reject another user's id without a join.

Completion percentage is `round(completed_tasks * 100 / total_tasks)` in the API. It is not stored as a column.

The migration is `backend/alembic/versions/0001_initial.py`.
