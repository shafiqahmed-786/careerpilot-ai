from app.catalog import normalize_role
from app.search import demo_resources


def test_unknown_role_uses_software_engineer_rubric() -> None:
    key, title = normalize_role("Underwater basket weaver")
    assert key == "software engineer"
    assert title == "Software Engineer"


def test_demo_resources_are_real_https_links_and_labelled() -> None:
    resources = demo_resources("SQL", "Backend Engineer")
    assert resources
    for resource in resources:
        assert resource.provider == "demo"
        assert resource.url.startswith("https://")
        assert resource.domain
        assert "not a live search result" in resource.relevance
