# Product requirements

## Users

Students and fresh graduates who can name a target role and list skills they believe they have.

## Job to be done

Turn that profile into a saved study plan and show progress from tasks the user actually completes.

## In scope

1. Account creation and sign-in.
2. Career profile: education, experience level, skills with a 0–5 self-report, projects, target career, weekly hours, timeline of 4, 8, or 12 weeks.
3. Career assessment with a documented rubric, normalized role, gaps, and a reason to start with one skill.
4. Learning resources with title, URL, domain, snippet, skill, and why the item was kept. Live search when Tavily is configured. Otherwise a labelled demo catalog.
5. A persisted roadmap with week, objective, skills, tasks, time, resources, outcome, and completion criteria.
6. Task status, notes, and a dashboard whose completion percentage is computed from task rows.

## Out of scope

Resume parsing, interview practice, social features, mentoring, calendars, and advanced analytics.

## Honesty rules

- Self-reported proficiency is not verified competence.
- Demo resources are not described as live search.
- The product does not invent resource URLs.

## Success

A signed-in user can go from an empty profile to a stored roadmap and see the dashboard change after completing a task, with the worker running in a separate process.
