"""Canonical-URL smoke checks for the Practical AI Journey FastAPI app.

Run from the repo root with the project venv active::

    python _hermes_verify_canonical_urls.py

The script verifies, for every public page in both root and subpath modes:
  - the route returns HTTP 200
  - exactly one ``<link rel="canonical" href="...">`` tag is rendered in
    the document ``<head>``
  - that tag's href matches the expected apex-domain canonical target
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from os import environ

from fastapi.testclient import TestClient

ROOT_PATH = "/projects/practical-ai-journey"

CANONICAL_DOMAIN = "https://davidkendrick.dev"

# Map of public route -> expected canonical URL. Both the ``*.html`` primary
# form and the extensionless alias point at the same apex canonical target.
EXPECTED_CANONICAL = {
    "/": f"{CANONICAL_DOMAIN}/",
    "/index.html": f"{CANONICAL_DOMAIN}/",
    "/manitoba-cottage-search.html": f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
    "/manitoba-cottage-search": f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
    "/student-assignment-tracker.html": (
        f"{CANONICAL_DOMAIN}/student-assignment-tracker.html"
    ),
    "/student-assignment-tracker": (
        f"{CANONICAL_DOMAIN}/student-assignment-tracker.html"
    ),
    "/hermes-workflow.html": f"{CANONICAL_DOMAIN}/hermes-workflow.html",
    "/hermes-workflow": f"{CANONICAL_DOMAIN}/hermes-workflow.html",
    "/local-models-benchmarking.html": (
        f"{CANONICAL_DOMAIN}/local-models-benchmarking.html"
    ),
    "/local-models-benchmarking": (
        f"{CANONICAL_DOMAIN}/local-models-benchmarking.html"
    ),
}

# Match a single canonical tag across its possible attribute orderings.
CANONICAL_TAG_RE = re.compile(
    r"""<link\b[^>]*\brel\s*=\s*["']canonical["'][^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*/?>"""
    r"""|<link\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*\brel\s*=\s*["']canonical["'][^>]*/?>""",
    re.IGNORECASE,
)


def extract_canonical_hrefs(html: str) -> list[str]:
    """Return the href of every ``<link rel="canonical">`` tag in ``html``."""
    matches = CANONICAL_TAG_RE.findall(html)
    return [href for pair in matches for href in pair if href]


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
    # Import inside the configured environment so app settings are read after
    # PRACTICAL_AI_ROOT_PATH is set for this check. Clear app modules between
    # modes because Starlette/Jinja URL generation can otherwise retain state
    # from the previous root_path configuration inside this one process.
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

        for route, expected_canonical in EXPECTED_CANONICAL.items():
            response = client.get(route)
            if response.status_code != 200:
                raise AssertionError(
                    f"{label} {route}: expected 200, got {response.status_code}"
                )

            canonical_hrefs = extract_canonical_hrefs(response.text)
            if len(canonical_hrefs) == 0:
                raise AssertionError(
                    f"{label} {route}: missing <link rel=canonical> tag"
                )
            if len(canonical_hrefs) > 1:
                raise AssertionError(
                    f"{label} {route}: expected exactly one canonical tag, "
                    f"got {len(canonical_hrefs)}: {canonical_hrefs!r}"
                )

            actual = canonical_hrefs[0]
            if actual != expected_canonical:
                raise AssertionError(
                    f"{label} {route}: canonical mismatch "
                    f"expected {expected_canonical!r}, got {actual!r}"
                )

            print(f"[PASS] {label} {route} -> {actual}")


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("All canonical-URL checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())