# AI engineering decisions

## Pipeline

`profile → normalize role → score gaps → discover resources → narrative → roadmap → PostgreSQL`

Scoring and URL selection are deterministic code. The optional model call rewrites two text fields: `summary` and `learn_first_reason`. If that call is missing, invalid, or fails, the template narrative is stored and `provider` is `demo`.

## Rubric `importance-x-gap-v1`

- `importance` is 1–5 for the role.
- `target_level` is a study target, not a certification.
- `self_reported_level` is copied from the profile. Unlisted skills are 0.
- `gap = max(0, target_level - self_reported_level)`
- `priority_score = importance * gap`
- `missing`: self-reported level is 0.
- `improve`: reported, but below the target.
- `sufficient`: reported at or above the target.

The assessment stores this disclaimer: self-reported levels are not an objective measure of competence.

## Web search instead of RAG

The resources a student needs are public and change: documentation, course pages, and tutorials. A web search returns those URLs directly. RAG would require a corpus we do not have. It becomes useful when the product retrieves the user's own notes, syllabi, or a curated internal library, where the answer depends on private text rather than the open web.

## Attribution

Each resource row stores title, URL, domain, snippet, skill, provider (`tavily` or `demo`), and a relevance sentence written by the application. The roadmap copies those URLs onto tasks. The narrative schema has no URL field, so a model response cannot add a link.

## Untrusted pages

Snippets are truncated and placed inside `<untrusted_page>` tags. The system prompt tells the model to treat that text as data and to ignore instructions inside it. Only `https` URLs are kept. A unit test checks that extra JSON fields such as `url` and `instruction` are dropped by the narrative schema.

## Failure behaviour

- OpenAI missing, invalid output, or any error: the template narrative is stored with `provider=demo`; the job still completes.
- Tavily missing, erroring, or returning no usable `https` results: the demo catalog is used for that skill and labelled `demo`.
- Resource discovery and the roadmap use the same focus-skill list (`focus_skills`), so every roadmap task has resources.

## Providers

- LLM: OpenAI Chat Completions when `OPENAI_API_KEY` is set. Otherwise the template.
- Search: Tavily when `TAVILY_API_KEY` is set. Otherwise `app/catalog.py` resources, labelled demo.

## v2: mentor, AI roadmap, resume intelligence

- **Structured outputs.** Roadmap and resume responses are parsed into Pydantic models (`AIRoadmap`, `ResumeAnalysisResult`) with length and range limits; extra fields are ignored; any failure triggers the labelled fallback.
- **Context engineering.** The mentor receives a summary (profile, top 6 gaps, roadmap counts, next 3 tasks, recent completions, skipped tasks, resume skill names) plus the last 8 messages, not rows or whole histories.
- **Deterministic boundaries.** Gap scores, readiness, resume match, streaks and authorization are Python. The model writes text and extracts evidence.
- **Grounding.** Roadmap resources come only from the provided list (unknown URLs dropped; tasks without a valid URL get verified resources for their first skill). Resume evidence quotes must exist in the resume text, otherwise the skill is downgraded.
- **Prompt injection.** Profile text, resume text and web snippets sit inside delimited tags that the system prompt declares to be data. Outputs are validated, so an injected instruction cannot add URLs, scores, or unknown skills.
- **Provider transparency.** `provider` is stored on assessments, roadmaps, resume analyses and every mentor message; the UI shows it. Template replies state they are templates.
- **Fallbacks.** No key, timeout, HTTP error, invalid JSON or failed validation each lead to the deterministic path; the job still completes.
- **Cost.** One call per operation; `max_tokens` bounded; no retries; no extra calls.
- **No frameworks.** Direct HTTP to the OpenAI API; no LangChain, agents or vector store.
- **Adaptation rule.** Every 6 completed hours on a skill raise its planning level by one (capped at the target) to re-rank focus skills. This is a transparent heuristic, documented as such.
