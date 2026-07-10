"""Issue #28 smoke check: every public page renders the required Open Graph
and Twitter card metadata, with og:url equal to canonical_url.

Run from the repo root with the project venv active::

    python _hermes_verify_issue_28_og_twitter_metadata.py

The script verifies, for every public page in both root and subpath modes:
  - the route returns HTTP 200
  - exactly one of each required tag is rendered in <head>:
      og:title, og:description, og:url, og:type, og:site_name,
      twitter:card, twitter:title, twitter:description
  - og:url equals the expected apex-domain canonical URL
  - og:title matches "<title> | David Kendrick" (where <title> is the
    page title context value)
  - og:description matches the page description context value
  - twitter:title / twitter:description mirror the same values
  - og:type matches the route's expected value (homepage -> "website",
    case-study pages -> "article")
  - twitter:card equals "summary"
  - og:site_name equals "David Kendrick"
  - no duplicate/conflicting tags are rendered
  - no og:image tag is rendered (none exists as a stable public asset)
"""

from __future__ import annotations

import html
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from os import environ

from fastapi.testclient import TestClient

ROOT_PATH = "/projects/practical-ai-journey"

CANONICAL_DOMAIN = "https://davidkendrick.dev"

PUBLIC_ROUTES = [
    "/",
    "/index.html",
    "/manitoba-cottage-search.html",
    "/manitoba-cottage-search",
    "/student-assignment-tracker.html",
    "/student-assignment-tracker",
    "/hermes-workflow.html",
    "/hermes-workflow",
    "/local-models-benchmarking.html",
    "/local-models-benchmarking",
]

# Map of public route -> (expected title, expected description,
# expected canonical_url, expected og_type).
EXPECTED_META = {
    "/": (
        "Building Practical AI Systems",
        "Hands-on work by David Kendrick on practical AI systems: agents, "
        "workflow design, local model experiments, and browser automation.",
        f"{CANONICAL_DOMAIN}/",
        "website",
    ),
    "/index.html": (
        "Building Practical AI Systems",
        "Hands-on work by David Kendrick on practical AI systems: agents, "
        "workflow design, local model experiments, and browser automation.",
        f"{CANONICAL_DOMAIN}/",
        "website",
    ),
    "/manitoba-cottage-search.html": (
        "Manitoba Cottage Search",
        "How David Kendrick built Manitoba Cottage Search: a FastAPI and "
        "HTMX app with structured intake, browser-backed extraction, and "
        "agent-assisted workflow.",
        f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
        "article",
    ),
    "/manitoba-cottage-search": (
        "Manitoba Cottage Search",
        "How David Kendrick built Manitoba Cottage Search: a FastAPI and "
        "HTMX app with structured intake, browser-backed extraction, and "
        "agent-assisted workflow.",
        f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
        "article",
    ),
    "/student-assignment-tracker.html": (
        "Student Assignment Tracker",
        "How David Kendrick built a Student Assignment Tracker: an "
        "education tracker on FastAPI, SQLite, and HTMX, with an "
        "agent-assisted workflow.",
        f"{CANONICAL_DOMAIN}/student-assignment-tracker.html",
        "article",
    ),
    "/student-assignment-tracker": (
        "Student Assignment Tracker",
        "How David Kendrick built a Student Assignment Tracker: an "
        "education tracker on FastAPI, SQLite, and HTMX, with an "
        "agent-assisted workflow.",
        f"{CANONICAL_DOMAIN}/student-assignment-tracker.html",
        "article",
    ),
    "/hermes-workflow.html": (
        "How I Structured My AI Agent Workflow",
        "David Kendrick's Hermes workflow: profiles, memory, skills, "
        "model routing, and review gates for practical AI work.",
        f"{CANONICAL_DOMAIN}/hermes-workflow.html",
        "article",
    ),
    "/hermes-workflow": (
        "How I Structured My AI Agent Workflow",
        "David Kendrick's Hermes workflow: profiles, memory, skills, "
        "model routing, and review gates for practical AI work.",
        f"{CANONICAL_DOMAIN}/hermes-workflow.html",
        "article",
    ),
    "/local-models-benchmarking.html": (
        "Local Models and Benchmarking on a Mac Mini",
        "How David Kendrick runs local models on a Mac Mini: Ollama, MLX, "
        "oMLX, and a repeatable coding benchmark for practical model work.",
        f"{CANONICAL_DOMAIN}/local-models-benchmarking.html",
        "article",
    ),
    "/local-models-benchmarking": (
        "Local Models and Benchmarking on a Mac Mini",
        "How David Kendrick runs local models on a Mac Mini: Ollama, MLX, "
        "oMLX, and a repeatable coding benchmark for practical model work.",
        f"{CANONICAL_DOMAIN}/local-models-benchmarking.html",
        "article",
    ),
}

REQUIRED_OG_TAGS = (
    "title",
    "description",
    "url",
    "type",
    "site_name",
)
REQUIRED_TWITTER_TAGS = (
    "card",
    "title",
    "description",
)
ALL_REQUIRED_TAGS = REQUIRED_OG_TAGS + REQUIRED_TWITTER_TAGS

# Match meta tags in either attribute order. Use a list of tuples
# ``(regex_compiled, tag_name)`` so we can attribute-order-agnostically pick
# out each tag and gather the value of ``content``.
META_TAG_RE = re.compile(
    r"<meta\b[^>]*\bproperty\s*=\s*[\"']og:([a-zA-Z_:-]+)[\"'][^>]*\bcontent\s*=\s*"
    r"[\"']([^\"']*)[\"'][^>]*/?>",
    re.IGNORECASE,
)
META_TAG_RE_OG_REV = re.compile(
    r"<meta\b[^>]*\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*\bproperty\s*=\s*"
    r"[\"']og:([a-zA-Z_:-]+)[\"'][^>]*/?>",
    re.IGNORECASE,
)
META_TAG_RE_NAME = re.compile(
    r"<meta\b[^>]*\bname\s*=\s*[\"']twitter:([a-zA-Z_:-]+)[\"'][^>]*\bcontent\s*=\s*"
    r"[\"']([^\"']*)[\"'][^>]*/?>",
    re.IGNORECASE,
)
META_TAG_RE_NAME_REV = re.compile(
    r"<meta\b[^>]*\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*\bname\s*=\s*"
    r"[\"']twitter:([a-zA-Z_:-]+)[\"'][^>]*/?>",
    re.IGNORECASE,
)


def collect_meta(html: str, prefix: str) -> dict[str, list[str]]:
    """Return ``{tag_local_name: [content, ...]}`` for every ``prefix:<name>``
    tag in ``html``. Multiple values per name flag duplicates.

    ``META_TAG_RE`` and ``META_TAG_RE_OG_REV`` already capture the body
    after ``og:``/``twitter:`` (e.g. group 1 is ``title``, not ``og:title``).
    """
    found: dict[str, list[str]] = {}

    if prefix == "og":
        for regex, idx_name, idx_value in (
            (META_TAG_RE, 1, 2),
            (META_TAG_RE_OG_REV, 2, 1),
        ):
            for match in regex.finditer(html):
                name = match.group(idx_name).lower()
                value = match.group(idx_value)
                found.setdefault(name, []).append(value)

    if prefix == "twitter":
        for regex, idx_name, idx_value in (
            (META_TAG_RE_NAME, 1, 2),
            (META_TAG_RE_NAME_REV, 2, 1),
        ):
            for match in regex.finditer(html):
                name = match.group(idx_name).lower()
                value = match.group(idx_value)
                found.setdefault(name, []).append(value)

    return found


@contextmanager
def configured_root_path(root_path: str | None) -> Iterator[None]:
    previous = environ.get("PRACTICAL_AI_ROOT_PATH")
    if root_path:
        environ["PRACTICAL_AI_ROOT_PATH"] = root_path
    else:
        environ.pop("PRACTICAL_AI_ROOT_PATH", None)
    try:
        yield
    finally:
        if previous is None:
            environ.pop("PRACTICAL_AI_ROOT_PATH", None)
        else:
            environ["PRACTICAL_AI_ROOT_PATH"] = previous


def build_client(root_path: str | None) -> TestClient:
    # Clear app modules so PRACTICAL_AI_ROOT_PATH is read fresh for each mode
    # (same pattern as the other verify scripts).
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    from app.main import create_app

    if root_path:
        return TestClient(create_app(), root_path=root_path)
    return TestClient(create_app())


def verify_route(
    client: TestClient, route: str, label: str,
    expected_title: str, expected_description: str,
    expected_canonical: str, expected_og_type: str,
) -> None:
    response = client.get(route)
    if response.status_code != 200:
        raise AssertionError(
            f"{label} {route}: expected 200, got {response.status_code}"
        )
    body = response.text

    expected_doc_title = f"{expected_title} | David Kendrick"

    og_meta = collect_meta(body, "og")
    tw_meta = collect_meta(body, "twitter")

    # Unescape HTML entities so apostrophes / quotes inside the text content
    # don't break comparisons against the spec strings (Jinja autoescape
    # emits ``&#39;`` for ``'`` inside attribute values).
    def _norm(value: str) -> str:
        return html.unescape(value)

    # Every required OG tag must exist exactly once.
    for tag in REQUIRED_OG_TAGS:
        values = og_meta.get(tag)
        if values is None:
            raise AssertionError(
                f"{label} {route}: missing required <meta property=\"og:{tag}\">"
            )
        if len(values) > 1:
            raise AssertionError(
                f"{label} {route}: duplicate og:{tag} tag "
                f"({len(values)} occurrences)"
            )

    # Every required Twitter tag must exist exactly once.
    for tag in REQUIRED_TWITTER_TAGS:
        values = tw_meta.get(tag)
        if values is None:
            raise AssertionError(
                f"{label} {route}: missing required "
                f"<meta name=\"twitter:{tag}\">"
            )
        if len(values) > 1:
            raise AssertionError(
                f"{label} {route}: duplicate twitter:{tag} tag "
                f"({len(values)} occurrences)"
            )

    # og:url must equal the page's canonical_url (canonical URLs are pure
    # ASCII so no unescape needed for that comparison).
    og_url = og_meta["url"][0]
    if og_url != expected_canonical:
        raise AssertionError(
            f"{label} {route}: og:url mismatch "
            f"expected {expected_canonical!r}, got {og_url!r}"
        )

    # og:title and twitter:title mirror the document <title> suffix.
    if _norm(og_meta["title"][0]) != expected_doc_title:
        raise AssertionError(
            f"{label} {route}: og:title mismatch "
            f"expected {expected_doc_title!r}, "
            f"got {og_meta['title'][0]!r}"
        )
    if _norm(tw_meta["title"][0]) != expected_doc_title:
        raise AssertionError(
            f"{label} {route}: twitter:title mismatch "
            f"expected {expected_doc_title!r}, "
            f"got {tw_meta['title'][0]!r}"
        )

    # og:description and twitter:description mirror the meta description.
    if _norm(og_meta["description"][0]) != expected_description:
        raise AssertionError(
            f"{label} {route}: og:description mismatch "
            f"expected {expected_description!r}, "
            f"got {og_meta['description'][0]!r}"
        )
    if _norm(tw_meta["description"][0]) != expected_description:
        raise AssertionError(
            f"{label} {route}: twitter:description mismatch "
            f"expected {expected_description!r}, "
            f"got {tw_meta['description'][0]!r}"
        )

    # og:type matches the route's expected value (ASCII only, no unescape).
    if og_meta["type"][0] != expected_og_type:
        raise AssertionError(
            f"{label} {route}: og:type mismatch "
            f"expected {expected_og_type!r}, "
            f"got {og_meta['type'][0]!r}"
        )

    # og:site_name pinned to "David Kendrick" (ASCII only).
    if og_meta["site_name"][0] != "David Kendrick":
        raise AssertionError(
            f"{label} {route}: og:site_name mismatch "
            f"expected 'David Kendrick', got {og_meta['site_name'][0]!r}"
        )

    # twitter:card pinned to "summary" (ASCII only).
    if tw_meta["card"][0] != "summary":
        raise AssertionError(
            f"{label} {route}: twitter:card mismatch "
            f"expected 'summary', got {tw_meta['card'][0]!r}"
        )

    # No OG image tag rendered (none exists as a stable public asset).
    if "image" in og_meta:
        raise AssertionError(
            f"{label} {route}: og:image must not be rendered "
            f"(no stable public image asset exists)"
        )
    if "image" in tw_meta:
        raise AssertionError(
            f"{label} {route}: twitter:image must not be rendered "
            f"(no stable public image asset exists)"
        )

    print(
        f"[PASS] {label} {route} og:url={og_url} og:type={og_meta['type'][0]}"
    )


def verify_mode(label: str, root_path: str | None) -> None:
    with configured_root_path(root_path):
        client = build_client(root_path)
        for route in PUBLIC_ROUTES:
            (
                expected_title,
                expected_description,
                expected_canonical,
                expected_og_type,
            ) = EXPECTED_META[route]
            verify_route(
                client,
                route,
                label,
                expected_title,
                expected_description,
                expected_canonical,
                expected_og_type,
            )


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("Issue #28 OG/Twitter metadata checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
