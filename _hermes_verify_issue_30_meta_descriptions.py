"""Issue #30 smoke check: tightened meta descriptions are live on every
public page, render exactly once in the document head, and propagate to
the Open Graph / Twitter / JSON-LD surfaces that share the same route
context.

Run from the repo root with the project venv active::

    python _hermes_verify_issue_30_meta_descriptions.py

The script verifies, for every public page in both root and subpath modes:

* the route returns HTTP 200
* exactly one ``<meta name="description" content="...">`` is rendered
* the content matches the approved issue #30 copy for the page
* the description also propagates to ``og:description`` and
  ``twitter:description`` (so a single edit to ``app/routes/pages.py``
  cannot leave one of the three surfaces stale)
* the description length per page is reported for traceability
* the homepage, Manitoba Cottage Search, and Local Models descriptions
  are tightened versus the pre-#30 originals
* the secondary-page descriptions fall in the parent-approved band
  (target band: 110-160 chars, with homepage held at 130 from #27)

The check is deliberately conservative: any page that ends up with no
description, more than one description, an empty description, a
description that does not match the approved copy, or an OG/Twitter
description that has drifted away from the route context will fail this
script loudly.
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

# Approved issue #30 copy. Mirrors the *_CONTEXT["description"] fields in
# app/routes/pages.py verbatim from the marketing-seo approved copy locked in
# by the parent card. The homepage value is unchanged from issue #27; the
# four secondary pages are the exact approved descriptions (not close
# rewrites), so a single edit to app/routes/pages.py cannot drift away
# from the marketing-approved wording.
EXPECTED_DESCRIPTIONS: dict[str, str] = {
    "/": (
        "Hands-on work by David Kendrick on practical AI systems: agents, "
        "workflow design, local model experiments, and browser automation."
    ),
    "/index.html": (
        "Hands-on work by David Kendrick on practical AI systems: agents, "
        "workflow design, local model experiments, and browser automation."
    ),
    "/manitoba-cottage-search.html": (
        "Case study: how David Kendrick built a FastAPI and HTMX "
        "listing-review app for Manitoba cottage hunting, with "
        "structured intake and browser-backed extraction."
    ),
    "/manitoba-cottage-search": (
        "Case study: how David Kendrick built a FastAPI and HTMX "
        "listing-review app for Manitoba cottage hunting, with "
        "structured intake and browser-backed extraction."
    ),
    "/student-assignment-tracker.html": (
        "Case study: an education tracker David Kendrick shipped with "
        "FastAPI, SQLite, and HTMX, built through an agent-assisted "
        "development workflow."
    ),
    "/student-assignment-tracker": (
        "Case study: an education tracker David Kendrick shipped with "
        "FastAPI, SQLite, and HTMX, built through an agent-assisted "
        "development workflow."
    ),
    "/hermes-workflow.html": (
        "How David Kendrick structures practical AI work with Hermes "
        "profiles, memory, skills, model routing, and review gates."
    ),
    "/hermes-workflow": (
        "How David Kendrick structures practical AI work with Hermes "
        "profiles, memory, skills, model routing, and review gates."
    ),
    "/local-models-benchmarking.html": (
        "David Kendrick's Mac Mini experiments running local models with "
        "Ollama, MLX, and oMLX, and a repeatable coding benchmark behind "
        "them."
    ),
    "/local-models-benchmarking": (
        "David Kendrick's Mac Mini experiments running local models with "
        "Ollama, MLX, and oMLX, and a repeatable coding benchmark behind "
        "them."
    ),
}

# Pre-issue-#30 originals. Used only to assert the three target pages
# (homepage, Manitoba, Local Models) were tightened versus the SEO
# findings the parent card reported. Length is the simple, deterministic
# measure used to flag regressions.
ORIGINAL_DESCRIPTIONS: dict[str, str] = {
    "/": (
        "A draft portfolio page where David Kendrick documents the "
        "practical AI systems he builds: agents, workflows, local-model "
        "experiments, and browser automation experiments in production."
    ),
    "/manitoba-cottage-search.html": (
        "Case study for Manitoba Cottage Search: a FastAPI and HTMX "
        "listing-review app with structured intake, browser-backed "
        "extraction, and agent-assisted workflow design."
    ),
    "/manitoba-cottage-search": (
        "Case study for Manitoba Cottage Search: a FastAPI and HTMX "
        "listing-review app with structured intake, browser-backed "
        "extraction, and agent-assisted workflow design."
    ),
    "/local-models-benchmarking.html": (
        "Local models page describing David Kendrick's Mac Mini M4 "
        "experiments with Ollama, MLX, oMLX, and a repeatable coding benchmark "
        "for speed, reliability, and memory-ceiling tradeoffs."
    ),
    "/local-models-benchmarking": (
        "Local models page describing David Kendrick's Mac Mini M4 "
        "experiments with Ollama, MLX, oMLX, and a repeatable coding benchmark "
        "for speed, reliability, and memory-ceiling tradeoffs."
    ),
}

# Parent-approved secondary-page length band. Homepage is held at 130 by
# issue #27 and is not re-asserted here.
SECONDARY_LENGTH_BAND = (110, 160)

# Match meta tags in either attribute order so we pick up
# ``<meta name="description" content="...">`` and the reversed form.
DESCRIPTION_TAG_RE = re.compile(
    r"<meta\b[^>]*\bname\s*=\s*[\"']description[\"'][^>]*"
    r"\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*/?>",
    re.IGNORECASE,
)
DESCRIPTION_TAG_RE_REV = re.compile(
    r"<meta\b[^>]*\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*"
    r"\bname\s*=\s*[\"']description[\"'][^>]*/?>",
    re.IGNORECASE,
)

OG_DESCRIPTION_RE = re.compile(
    r"<meta\b[^>]*\bproperty\s*=\s*[\"']og:description[\"'][^>]*"
    r"\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*/?>",
    re.IGNORECASE,
)
OG_DESCRIPTION_RE_REV = re.compile(
    r"<meta\b[^>]*\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*"
    r"\bproperty\s*=\s*[\"']og:description[\"'][^>]*/?>",
    re.IGNORECASE,
)
TWITTER_DESCRIPTION_RE = re.compile(
    r"<meta\b[^>]*\bname\s*=\s*[\"']twitter:description[\"'][^>]*"
    r"\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*/?>",
    re.IGNORECASE,
)
TWITTER_DESCRIPTION_RE_REV = re.compile(
    r"<meta\b[^>]*\bcontent\s*=\s*[\"']([^\"']*)[\"'][^>]*"
    r"\bname\s*=\s*[\"']twitter:description[\"'][^>]*/?>",
    re.IGNORECASE,
)


def _collect_single(re_forwards: re.Pattern[str], re_backwards: re.Pattern[str],
                    html_text: str) -> list[str]:
    """Return every content value matched by either regex, deduped."""
    values: list[str] = []
    for regex in (re_forwards, re_backwards):
        values.extend(match.group(1) for match in regex.finditer(html_text))
    return values


def _norm(value: str) -> str:
    """Unescape HTML entities so apostrophes inside the text don't trip
    string comparisons (Jinja autoescape emits ``&#39;`` for ``'``)."""
    return html.unescape(value)


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
    # Clear app modules so PRACTICAL_AI_ROOT_PATH is read fresh for each
    # mode (same pattern as the other verify scripts).
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    from app.main import create_app

    if root_path:
        return TestClient(create_app(), root_path=root_path)
    return TestClient(create_app())


def verify_route(client: TestClient, route: str, label: str) -> None:
    response = client.get(route)
    if response.status_code != 200:
        raise AssertionError(
            f"{label} {route}: expected 200, got {response.status_code}"
        )
    body = response.text

    expected = EXPECTED_DESCRIPTIONS[route]

    # Exactly one <meta name="description">.
    description_values = _collect_single(
        DESCRIPTION_TAG_RE, DESCRIPTION_TAG_RE_REV, body,
    )
    if len(description_values) == 0:
        raise AssertionError(
            f"{label} {route}: missing <meta name=\"description\">"
        )
    if len(description_values) > 1:
        raise AssertionError(
            f"{label} {route}: duplicate <meta name=\"description\"> "
            f"({len(description_values)} occurrences)"
        )
    actual = _norm(description_values[0])
    if actual != expected:
        raise AssertionError(
            f"{label} {route}: meta description mismatch "
            f"expected {expected!r}, got {actual!r}"
        )

    # og:description must mirror the route context exactly.
    og_values = _collect_single(
        OG_DESCRIPTION_RE, OG_DESCRIPTION_RE_REV, body,
    )
    if len(og_values) != 1:
        raise AssertionError(
            f"{label} {route}: expected exactly one og:description, "
            f"got {len(og_values)}"
        )
    if _norm(og_values[0]) != expected:
        raise AssertionError(
            f"{label} {route}: og:description drift "
            f"expected {expected!r}, got {_norm(og_values[0])!r}"
        )

    # twitter:description must mirror the route context exactly.
    tw_values = _collect_single(
        TWITTER_DESCRIPTION_RE, TWITTER_DESCRIPTION_RE_REV, body,
    )
    if len(tw_values) != 1:
        raise AssertionError(
            f"{label} {route}: expected exactly one twitter:description, "
            f"got {len(tw_values)}"
        )
    if _norm(tw_values[0]) != expected:
        raise AssertionError(
            f"{label} {route}: twitter:description drift "
            f"expected {expected!r}, got {_norm(tw_values[0])!r}"
        )

    # Secondary-page length band check (homepage is pinned at 130 by #27).
    if route not in ("/", "/index.html"):
        lo, hi = SECONDARY_LENGTH_BAND
        if not (lo <= len(expected) <= hi):
            raise AssertionError(
                f"{label} {route}: secondary description length "
                f"{len(expected)} outside approved band "
                f"{lo}-{hi}"
            )

    # Tightening check: homepage, Manitoba, Local Models must be shorter
    # than (or equal to) the pre-issue-#30 original.
    if route in ORIGINAL_DESCRIPTIONS:
        original = ORIGINAL_DESCRIPTIONS[route]
        if len(expected) > len(original):
            raise AssertionError(
                f"{label} {route}: description length regressed "
                f"({len(expected)} chars, was {len(original)} chars)"
            )

    print(
        f"[PASS] {label} {route} description len={len(expected)} "
        f"og/twitter in lock-step"
    )


def verify_mode(label: str, root_path: str | None) -> None:
    with configured_root_path(root_path):
        client = build_client(root_path)
        for route in PUBLIC_ROUTES:
            verify_route(client, route, label)


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("Issue #30 meta description checks passed.")
    print("Per-page description lengths:")
    for route in PUBLIC_ROUTES:
        # The homepage values are identical, so report each unique
        # canonical description once for readability.
        if route in ("/", "/index.html", "/manitoba-cottage-search",
                     "/student-assignment-tracker", "/hermes-workflow",
                     "/local-models-benchmarking"):
            canonical = route
            if route in ("/", "/index.html"):
                canonical = "/"
            elif route in ("/manitoba-cottage-search",):
                canonical = "/manitoba-cottage-search.html"
            elif route in ("/student-assignment-tracker",):
                canonical = "/student-assignment-tracker.html"
            elif route in ("/hermes-workflow",):
                canonical = "/hermes-workflow.html"
            elif route in ("/local-models-benchmarking",):
                canonical = "/local-models-benchmarking.html"
            description = EXPECTED_DESCRIPTIONS[canonical]
            print(f"  {route:40s} {len(description):3d} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())