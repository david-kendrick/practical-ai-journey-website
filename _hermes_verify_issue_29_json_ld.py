"""Issue #29 smoke check: every public page renders conservative,
factual JSON-LD structured data.

Run from the repo root with the project venv active::

    python _hermes_verify_issue_29_json_ld.py

The script verifies, for every public page in both root and subpath
modes:

* exactly one ``<script type="application/ld+json">`` block is rendered
* the JSON-LD payload parses as a single valid JSON object (or array)
* the payload contains *no* disallowed origins (``127.0.0.1``, ``www.``,
  ``/projects/practical-ai-journey/`` fallback) — only public apex
  canonical URLs
* the homepage graph (``/`` and ``/index.html``) is a ``@graph``
  containing both ``Person`` (David Kendrick) and ``WebSite``
* every secondary page (``og_type == "article"`` routes) emits a single
  ``CreativeWork`` or ``Article`` node
* the Person / author reference ``@id`` is the shared
  ``https://davidkendrick.dev/#person`` anchor used across the site
* existing smoke / canonical / robots / sitemap / OG-Twitter / issue #27
  / issue #28 contracts continue to pass (the verification here is
  independent — they are re-run by the orchestrator after this slice
  merges)

The check is deliberately conservative: any invented credential,
employer, organization, date, rating, review, offer, logo, or image
flag is allowed to fail this script as soon as it surfaces. ``BreadcrumbList``
is *not* expected and is flagged if present.
"""

from __future__ import annotations

import json
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

HOMEPAGE_ROUTES = ("/", "/index.html")

# Map of public route -> (expected title, expected description,
# expected canonical_url, expected og_type). Mirrors the canonical-URL
# and OG/Twitter verify scripts so JSON-LD stays in lock-step with the
# rest of the site's metadata contract.
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
        "Case study for Manitoba Cottage Search: a FastAPI and HTMX "
        "listing-review app with structured intake, browser-backed "
        "extraction, and agent-assisted workflow design.",
        f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
        "article",
    ),
    "/manitoba-cottage-search": (
        "Manitoba Cottage Search",
        "Case study for Manitoba Cottage Search: a FastAPI and HTMX "
        "listing-review app with structured intake, browser-backed "
        "extraction, and agent-assisted workflow design.",
        f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
        "article",
    ),
    "/student-assignment-tracker.html": (
        "Student Assignment Tracker",
        "Case study for a Student Assignment Tracker: an education tracker "
        "built with FastAPI, SQLite, HTMX, and an agent-assisted development "
        "workflow.",
        f"{CANONICAL_DOMAIN}/student-assignment-tracker.html",
        "article",
    ),
    "/student-assignment-tracker": (
        "Student Assignment Tracker",
        "Case study for a Student Assignment Tracker: an education tracker "
        "built with FastAPI, SQLite, HTMX, and an agent-assisted development "
        "workflow.",
        f"{CANONICAL_DOMAIN}/student-assignment-tracker.html",
        "article",
    ),
    "/hermes-workflow.html": (
        "How I Structured My AI Agent Workflow",
        "Agent workflow page describing how David Kendrick uses Hermes "
        "profiles, memory, skills, model routing, and review gates to "
        "structure practical AI work.",
        f"{CANONICAL_DOMAIN}/hermes-workflow.html",
        "article",
    ),
    "/hermes-workflow": (
        "How I Structured My AI Agent Workflow",
        "Agent workflow page describing how David Kendrick uses Hermes "
        "profiles, memory, skills, model routing, and review gates to "
        "structure practical AI work.",
        f"{CANONICAL_DOMAIN}/hermes-workflow.html",
        "article",
    ),
    "/local-models-benchmarking.html": (
        "Local Models and Benchmarking on a Mac Mini",
        "Local models page describing David Kendrick's Mac Mini M4 "
        "experiments with Ollama, MLX, oMLX, and a repeatable coding benchmark "
        "for speed, reliability, and memory-ceiling tradeoffs.",
        f"{CANONICAL_DOMAIN}/local-models-benchmarking.html",
        "article",
    ),
    "/local-models-benchmarking": (
        "Local Models and Benchmarking on a Mac Mini",
        "Local models page describing David Kendrick's Mac Mini M4 "
        "experiments with Ollama, MLX, oMLX, and a repeatable coding benchmark "
        "for speed, reliability, and memory-ceiling tradeoffs.",
        f"{CANONICAL_DOMAIN}/local-models-benchmarking.html",
        "article",
    ),
}

# Origins that must never appear inside JSON-LD. ``127.0.0.1`` catches the
# local preview server; ``www.davidkendrick.dev`` catches any leftover
# www-redirect target; ``/projects/practical-ai-journey/`` catches the
# operational subpath fallback that must never be advertised as a
# canonical surface.
DISALLOWED_ORIGINS = (
    "127.0.0.1",
    "www.davidkendrick.dev",
    "/projects/practical-ai-journey/",
)

# Shared Person @id, exported from app.seo.schema so every schema.org
# ``author`` / ``publisher`` reference points at one well-defined
# identity. Keeping it asserted here protects against accidental
# divergence between the homepage graph and any secondary page.
PERSON_ID = f"{CANONICAL_DOMAIN}/#person"

JSON_LD_TAG_RE = re.compile(
    r'<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>'
    r"(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


def extract_json_ld_blocks(html: str) -> list[str]:
    """Return the inner text of every ``<script type="application/ld+json">``.

    Attribute order is intentionally tolerated (``<script
    type="...">`` and ``<script ... type="...">`` both match). Returned
    strings are the raw JSON payloads (not yet parsed).
    """
    return [match.group(1).strip() for match in JSON_LD_TAG_RE.finditer(html)]


def _assert_no_disallowed_origin(payload_text: str, route: str, label: str) -> None:
    """Fail loudly if any disallowed origin appears in the JSON-LD text.

    The check is intentionally text-based — it catches origins anywhere
    in the payload (string values, ``url`` fields, ``@id`` anchors)
    even if the parser would accept them.
    """
    for needle in DISALLOWED_ORIGINS:
        if needle in payload_text:
            raise AssertionError(
                f"{label} {route}: JSON-LD references disallowed origin "
                f"{needle!r}"
            )


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

    blocks = extract_json_ld_blocks(body)
    if len(blocks) != 1:
        raise AssertionError(
            f"{label} {route}: expected exactly one "
            f"<script type=\"application/ld+json\">, got {len(blocks)}"
        )

    raw = blocks[0]
    _assert_no_disallowed_origin(raw, route, label)

    # The payload must be valid JSON. ``json.loads`` accepts objects
    # and arrays; both shapes are valid JSON-LD roots.
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{label} {route}: JSON-LD payload is not valid JSON ({exc})"
        )

    # Homepage: single @graph object containing Person + WebSite.
    if route in HOMEPAGE_ROUTES:
        if not isinstance(payload, dict) or "@graph" not in payload:
            raise AssertionError(
                f"{label} {route}: homepage JSON-LD must be a single "
                f"object with @graph"
            )
        graph = payload.get("@graph")
        if not isinstance(graph, list) or len(graph) < 2:
            raise AssertionError(
                f"{label} {route}: homepage @graph must contain at "
                f"least 2 nodes, got {len(graph) if isinstance(graph, list) else type(graph).__name__}"
            )

        types = {
            node.get("@type") for node in graph if isinstance(node, dict)
        }
        if "Person" not in types:
            raise AssertionError(
                f"{label} {route}: homepage @graph is missing a Person node"
            )
        if "WebSite" not in types:
            raise AssertionError(
                f"{label} {route}: homepage @graph is missing a WebSite node"
            )

        # WebSite.publisher must reference the shared Person @id so the
        # graph is internally linked.
        website_nodes = [
            n for n in graph if isinstance(n, dict) and n.get("@type") == "WebSite"
        ]
        publishers = [
            n.get("publisher") for n in website_nodes if n.get("publisher")
        ]
        if not any(
            isinstance(pub, dict) and pub.get("@id") == PERSON_ID
            for pub in publishers
        ):
            raise AssertionError(
                f"{label} {route}: WebSite.publisher must reference "
                f"the shared Person @id ({PERSON_ID})"
            )

        # BreadcrumbList is explicitly not part of issue #29.
        if "BreadcrumbList" in types:
            raise AssertionError(
                f"{label} {route}: BreadcrumbList should not be present "
                f"in issue #29"
            )

        # Every URL field in the homepage graph must reference the
        # canonical apex domain.
        for node in graph:
            if not isinstance(node, dict):
                continue
            if "url" in node and isinstance(node["url"], str):
                if not node["url"].startswith(CANONICAL_DOMAIN):
                    raise AssertionError(
                        f"{label} {route}: Person/WebSite url must "
                        f"start with {CANONICAL_DOMAIN!r}, "
                        f"got {node['url']!r}"
                    )

        print(f"[PASS] {label} {route} homepage graph @graph/Person/WebSite")
        return

    # Secondary page: single CreativeWork / Article node.
    if not isinstance(payload, dict):
        raise AssertionError(
            f"{label} {route}: secondary page JSON-LD must be a dict, "
            f"got {type(payload).__name__}"
        )
    schema_type = payload.get("@type")
    if schema_type not in ("CreativeWork", "Article"):
        raise AssertionError(
            f"{label} {route}: expected @type CreativeWork or Article, "
            f"got {schema_type!r}"
        )
    # og_type == "article" must produce an Article node (and the reverse
    # is also expected so they stay in lock-step). og_type values other
    # than "article" fall back to CreativeWork per app.seo.schema.
    if expected_og_type == "article" and schema_type != "Article":
        raise AssertionError(
            f"{label} {route}: og_type=article must produce an Article "
            f"node, got {schema_type!r}"
        )
    if expected_og_type != "article" and schema_type != "CreativeWork":
        raise AssertionError(
            f"{label} {route}: og_type={expected_og_type!r} must produce "
            f"a CreativeWork node, got {schema_type!r}"
        )

    # headline / name / description / url must match the page's route
    # context exactly so JSON-LD cannot drift away from the document.
    name = payload.get("name")
    if name != expected_title:
        raise AssertionError(
            f"{label} {route}: JSON-LD name mismatch "
            f"expected {expected_title!r}, got {name!r}"
        )
    description = payload.get("description")
    if description != expected_description:
        raise AssertionError(
            f"{label} {route}: JSON-LD description mismatch "
            f"expected {expected_description!r}, got {description!r}"
        )
    url = payload.get("url")
    if url != expected_canonical:
        raise AssertionError(
            f"{label} {route}: JSON-LD url mismatch "
            f"expected {expected_canonical!r}, got {url!r}"
        )

    # Author must point at the shared Person @id.
    author = payload.get("author")
    if not isinstance(author, dict) or author.get("@id") != PERSON_ID:
        raise AssertionError(
            f"{label} {route}: JSON-LD author must reference the shared "
            f"Person @id ({PERSON_ID}), got {author!r}"
        )

    # BreadcrumbList is explicitly not part of issue #29.
    if schema_type == "BreadcrumbList":
        raise AssertionError(
            f"{label} {route}: BreadcrumbList should not be present "
            f"in issue #29"
        )

    print(f"[PASS] {label} {route} @type={schema_type}")


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

    print("Issue #29 JSON-LD structured-data checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
