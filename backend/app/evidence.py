"""Independent validation of resume skill evidence (pure standard library).

The model proposes a classification and a verbatim quote for each skill. This module decides whether
the quote really supports THAT skill, using only the resume text:

1. the quote must exist in the resume (after safe whitespace/quote normalization) as one passage;
2. the quote must itself name the skill (or a true synonym such as "Postgres" for "PostgreSQL"),
   so a quote about something else can never support the skill, and one generic quote cannot
   support several unrelated technologies;
3. for "demonstrated", the clause that names the skill must describe doing something with it
   (built, deployed, tested, ...) and must not be a weak claim ("familiar with"), and the passage
   must not be a skills list.

Anything that fails is downgraded: demonstrated -> listed (the skill is named in the resume)
-> inferred (it is not). Inferred skills carry no evidence and never count toward coverage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SECTION_WORDS = {
    "skills": "skills", "technical skills": "skills", "technologies": "skills", "tech stack": "skills",
    "experience": "experience", "work experience": "experience", "professional experience": "experience",
    "internship": "experience", "internships": "experience", "employment": "experience",
    "projects": "projects", "personal projects": "projects", "academic projects": "projects",
    "education": "education", "achievements": "achievements", "awards": "achievements",
    "certifications": "achievements", "summary": "summary", "profile": "summary",
}

# Only genuine spellings of the same technology. Related technologies are NOT synonyms.
SYNONYMS = [
    {"javascript", "js"}, {"typescript", "ts"}, {"kubernetes", "k8s"}, {"postgresql", "postgres"},
    {"react", "react.js", "reactjs"}, {"node.js", "nodejs", "node"}, {"python", "py"},
    {"scikit-learn", "sklearn"}, {"golang", "go language"}, {"c++", "cpp"}, {"ci/cd", "cicd"},
]

_BASE_VERBS = [
    "build", "implement", "develop", "deploy", "test", "integrate", "maintain", "design", "create", "automate",
    "migrate", "optimize", "configure", "train", "analyze", "analyse", "use", "reduce", "improve", "launch", "ship",
    "containerize", "orchestrate", "architect", "engineer", "refactor", "debug", "monitor", "scale", "manage",
    "power", "leverage", "apply", "contribute", "deliver", "produce", "query", "model", "visualize", "clean",
    "process", "extract", "evaluate", "benchmark", "lead", "run", "write", "set up", "provision", "operate",
]
_IRREGULAR = {"built", "wrote", "written", "led", "ran", "made", "shipped", "setup", "running", "using", "writing"}


def _forms(base: str) -> set[str]:
    stem = base[:-1] if base.endswith("e") else base
    return {base, base + "s", base + "ed", base + "d", stem + "ing", stem + "ed"}


USAGE_WORDS: set[str] = set(_IRREGULAR)
for _verb in _BASE_VERBS:
    USAGE_WORDS |= _forms(_verb)

WEAK_WORDS = {
    "familiar", "familiarity", "knowledge", "exposure", "learning", "learned", "basic", "beginner", "interested",
    "aware", "awareness", "coursework", "studied", "studying", "understanding", "introductory", "intro", "course",
}

_WORD = re.compile(r"[a-z0-9+#./-]+")


def norm(value: str) -> str:
    """Safe normalization: unify quotes/dashes, drop a leading bullet, collapse whitespace, lowercase."""
    value = value.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")
    value = re.sub(r"^[\s\-*\u2022\u25cf\u25aa\u2023\u2013>]+", "", value)
    return " ".join(value.lower().split())


def sections(text: str) -> list[tuple[str, str]]:
    current = "other"
    rows: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        label = re.sub(r"[^a-z ]", "", line.lower()).strip()
        if label in SECTION_WORDS and len(line) <= 40:
            current = SECTION_WORDS[label]
            continue
        rows.append((current, line))
    return rows


def skill_regexes(name: str) -> list[re.Pattern[str]]:
    base = norm(name)
    terms = {base}
    for group in SYNONYMS:
        if base in group:
            terms |= group
    return [
        re.compile(
            r"(?<![a-z0-9+#])" + re.escape(term) + r"(?:[ -]?v?\d+(?:\.\d+)*)?(?![a-z0-9+#])", re.IGNORECASE
        )
        for term in terms
        if term
    ]


def mentions(skill_patterns: list[re.Pattern[str]], text: str) -> bool:
    folded = norm(text)
    return any(pattern.search(folded) for pattern in skill_patterns)


def locate(quote: str, rows: list[tuple[str, str]]) -> tuple[int, int] | None:
    """Return the (first, last) resume line indexes holding the quote, or None if it is not in the resume.

    A quote may span at most three consecutive lines (one bullet or passage)."""
    needle = norm(quote)
    if len(needle) < 6:
        return None
    lines = [norm(line) for _, line in rows]
    for index, line in enumerate(lines):
        if needle in line:
            return index, index
    joined = ""
    spans: list[tuple[int, int]] = []
    for line in lines:
        spans.append((len(joined), len(joined) + len(line)))
        joined += line + " "
    pos = joined.find(needle)
    if pos < 0:
        return None
    end = pos + len(needle) - 1

    def line_of(offset: int) -> int:
        return next(i for i, (a, b) in enumerate(spans) if a <= offset <= b)

    first, last = line_of(pos), line_of(end)
    return (first, last) if last - first <= 2 else None


def is_list_like(line: str) -> bool:
    folded = norm(line)
    if ":" in folded[:30] and len(folded.split(":", 1)[1].split()) <= 25:
        folded = folded.split(":", 1)[1]
    tokens = [t.strip() for t in re.split(r"[,;|/\u2022\u00b7]| {2,}", folded) if t.strip()]
    if len(tokens) < 3:
        return False
    average = sum(len(t.split()) for t in tokens) / len(tokens)
    has_verb = any(word in USAGE_WORDS for word in _WORD.findall(folded))
    return average <= 3 and not has_verb


def _clauses(quote: str) -> list[str]:
    return [c for c in re.split(r"[;.\n\u2022]|\s[-\u2013\u2014]\s", norm(quote)) if c.strip()]


def shows_usage(skill_patterns: list[re.Pattern[str]], quote: str) -> bool:
    """The clause naming the skill must describe doing something with it, and not be a weak claim."""
    for clause in _clauses(quote):
        for pattern in skill_patterns:
            match = pattern.search(clause)
            if not match:
                continue
            words = _WORD.findall(clause)
            before = _WORD.findall(clause[: match.start()])[-5:]
            if any(word in WEAK_WORDS for word in before):
                continue
            if any(word in USAGE_WORDS for word in words):
                return True
    return False


@dataclass
class Verdict:
    level: str
    evidence: list[str] = field(default_factory=list)
    confidence: str = "low"
    reason: str = ""


def validate_skill(
    name: str,
    level: str,
    quotes: list[str],
    usage: str,
    rows: list[tuple[str, str]],
    full_text: str,
    claimed_confidence: str = "medium",
) -> Verdict:
    patterns = skill_regexes(name)
    named_in_resume = mentions(patterns, full_text)
    related: list[tuple[str, tuple[int, int]]] = []
    for quote in quotes[:3]:
        position = locate(quote, rows)
        if position is None:
            continue  # not in the resume
        if not mentions(patterns, quote):
            continue  # exists, but says nothing about this skill
        related.append((quote.strip()[:240], position))

    if level == "demonstrated":
        for quote, (first, last) in related:
            span = range(first, last + 1)
            if any(rows[i][0] == "skills" for i in span) or all(is_list_like(rows[i][1]) for i in span):
                continue
            if len(usage.strip()) < 10 or not shows_usage(patterns, quote):
                continue
            confidence = "high" if claimed_confidence == "high" else "medium"
            return Verdict("demonstrated", [quote], confidence, "usage evidence verified")
        level = "listed" if named_in_resume else "inferred"
        reason = "no verifiable usage evidence for this skill"
    else:
        reason = "downgraded" if level == "listed" and not named_in_resume else ""

    if level == "listed":
        if not named_in_resume:
            return Verdict("inferred", [], "low", reason or "skill is not named in the resume")
        return Verdict("listed", [q for q, _ in related][:1], "medium", reason or "named without usage evidence")
    return Verdict("inferred", [], "low", reason or "not explicitly supported")
