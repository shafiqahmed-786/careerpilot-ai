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

## Providers

- LLM: OpenAI Chat Completions when `OPENAI_API_KEY` is set. Otherwise the template.
- Search: Tavily when `TAVILY_API_KEY` is set. Otherwise `app/catalog.py` resources, labelled demo.
