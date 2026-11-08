# Product requirements

## Context

CareerPilot AI is an interview MVP for an AI-Native Software Engineer Trainee evaluation. The brief allowed a free choice of problem (an AI Career Coach was the suggested start) and required a new project in a fresh public GitHub repository with at least five or six meaningful components, built with AI coding agents, with specification and planning documents, tests, CI, a deployed link, and a README that explains the architecture and key engineering decisions. Expected effort: four days, one week at most.

## Users

Students and fresh graduates who can name a target role and list skills they believe they have.

## Job to be done

Turn that profile into a saved study plan and show progress from tasks the user actually completes.

## Requirement coverage

| Brief requirement | How the product meets it |
| --- | --- |
| Frontend | Next.js 15 App Router: landing, signup, login, onboarding, dashboard, roadmap |
| API | FastAPI under `/api/v1` |
| Database | PostgreSQL with Alembic migrations |
| Background worker / queue | Redis + RQ, separate `python -m app.worker` process |
| AI component | Rubric scoring, OpenAI narrative, Tavily resource discovery, demo fallbacks |
| Authentication | bcrypt + JWT, owner-scoped data |
| Docs | Everything in `docs/` plus the README |
| Tests, CI | Pytest, Vitest, GitHub Actions |
| Deployed link | Placeholder marker at the top of the README; the owner deploys |

## In scope

1. Account creation and sign-in with validation and clear errors.
2. Career profile: name, education, experience level, skills with a 0–5 self-report, projects, target career, weekly hours, timeline of 4, 8, or 12 weeks.
3. Career assessment with a documented rubric, normalized role, existing/missing/improve skills, priority scores, and a reason to start with one skill.
4. Learning resources with title, URL, domain, snippet, skill, and why the item was kept. Live search with Tavily; otherwise a labelled demo catalog.
5. A persisted roadmap with week, objective, skills, tasks, time, resources, outcome, and completion criteria.
6. Task status (pending / in progress / completed), notes, and a dashboard whose completion percentage is computed from task rows.
7. Visible job states (queued, running, completed, failed) with retry.

## Out of scope

Resume parsing, interview practice, social features, mentoring, calendars, advanced analytics, vector search.

## Honesty rules

- Self-reported proficiency is not verified competence.
- Demo resources are never described as live search.
- The product does not invent resource URLs.
- Scores are never produced by a language model.

## Success

A newly registered user can go from an empty profile to a stored roadmap and see the dashboard change after completing a task, with the worker in a separate process, with or without OpenAI and Tavily keys.

## v2 additions

| Feature | Scope |
| --- | --- |
| AI Career Mentor | Route `/mentor`; persistent conversations; answers use the user's profile, gaps, roadmap progress and resume evidence; explicit live/demo labelling |
| AI roadmap | LLM-written weekly plan validated against a schema; deterministic fallback; source recorded on the roadmap |
| Adaptive plan | Explicit revise / intensive / lighter / focus actions; completed history preserved |
| Resume Analyzer | Route `/resume-analyzer`; PDF/DOCX; evidence-based skills; deterministic role comparison; apply to profile |
| Application shell and dashboard | Sidebar navigation, real metrics (progress, skills, gaps, milestones, streak, activity, readiness) |

Out of scope for v2: resume editor, job applications, OCR, streaming replies, vector search, multi-agent orchestration.

Honesty rules extend to the new features: resume keywords are not proof of skill; demo outputs are labelled; no LLM-generated percentages; no invented URLs.
