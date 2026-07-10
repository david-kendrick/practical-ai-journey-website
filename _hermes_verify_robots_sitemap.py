"""Smoke checks for the robots.txt and sitemap.xml endpoints.

Run from the repo root with the project venv active::

    python _hermes_verify_robots_sitemap.py

The script verifies, for both root and ``/projects/practical-ai-journey``
mount modes:

* ``/robots.txt`` returns HTTP 200 with ``text/plain`` content, allows
  crawling, and points at the apex-domain sitemap URL.
* ``/sitemap.xml`` returns HTTP 200 with an ``application/xml`` response
  containing exactly the canonical, indexable public URLs.
* Forbidden URL forms (local preview hosts, ``www`` aliases, extensionless
  aliases, the operational ``/projects/practical-ai-journey/`` subpath
  fallback) never appear in the sitemap.
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
SITEMAP_URL = f"{CANONICAL_DOMAIN}/sitemap.xml"

EXPECTED_SITEMAP_LOCS = [
    f"{CANONICAL_DOMAIN}/",
    f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
    f"{CANONICAL_DOMAIN}/student-assignment-tracker.html",
    f"{CANONICAL_DOMAIN}/hermes-workflow.html",
    f"{CANONICAL_DOMAIN}/local-models-benchmarking.html",
]

FORBIDDEN_SITEMAP_HINTS = [
    # Local preview hosts (uvicorn/127.0.0.1).
    "127.0.0.1",
    "localhost",
    # Operational subpath fallback.
    "/projects/practical-ai-journey/",
    # Apex www alias (only the apex is canonical today).
    "www.davidkendrick.dev",
    # Extensionless aliases should never advertise themselves.
    f"{CANONICAL_DOMAIN}/manitoba-cottage-search\n",
    f"{CANONICAL_DOMAIN}/manitoba-cottage-search\"",
    f"{CANONICAL_DOMAIN}/student-assignment-tracker\n",
    f"{CANONICAL_DOMAIN}/student-assignment-tracker\"",
    f"{CANONICAL_DOMAIN}/hermes-workflow\n",
    f"{CANONICAL_DOMAIN}/hermes-workflow\"",
    f"{CANONICAL_DOMAIN}/local-models-benchmarking\n",
    f"{CANONICAL_DOMAIN}/local-models-benchmarking\"",
]


# Capture the text inside each ``<loc>...</loc>`` element regardless of
# indentation or attribute ordering. Whitespace-tolerant and Python
# re.X-friendly so future edits to the sitemap template don't break
# this check.
SITEMAP_LOC_RE = re.compile(
    r"<loc\b[^>]*>(.*?)</loc>",
    re.IGNORECASE | re.DOTALL,
)


def extract_sitemap_locs(xml: str) -> list[str]:
    """Return the trimmed text of every ``<loc>`` element in ``xml``."""
    return [match.strip() for match in SITEMAP_LOC_RE.findall(xml)]


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
    # Clear app modules so PRACTICAL_AI_ROOT_PATH is read fresh inside
    # this process for each mode (matches the other verification scripts).
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    from app.main import create_app

    if root_path:
        return TestClient(create_app(), root_path=root_path)
    return TestClient(create_app())


def verify_robots(client: TestClient, label: str) -> None:
    response = client.get("/robots.txt")
    if response.status_code != 200:
        raise AssertionError(
            f"{label} /robots.txt: expected 200, got {response.status_code}"
        )
    content_type = response.headers.get("content-type", "")
    if "text/plain" not in content_type:
        raise AssertionError(
            f"{label} /robots.txt: unexpected content-type {content_type!r}"
        )
    body = response.text
    if not body.startswith("User-agent: *"):
        raise AssertionError(
            f"{label} /robots.txt: missing leading User-agent directive"
        )
    if "Disallow: /" in body:
        raise AssertionError(
            f"{label} /robots.txt: response must not blanket-disallow crawling"
        )
    if SITEMAP_URL not in body:
        raise AssertionError(
            f"{label} /robots.txt: missing sitemap pointer {SITEMAP_URL!r}"
        )
    print(f"[PASS] {label} /robots.txt -> {content_type}")


def verify_sitemap(client: TestClient, label: str) -> None:
    response = client.get("/sitemap.xml")
    if response.status_code != 200:
        raise AssertionError(
            f"{label} /sitemap.xml: expected 200, got {response.status_code}"
        )
    content_type = response.headers.get("content-type", "")
    if "xml" not in content_type:
        raise AssertionError(
            f"{label} /sitemap.xml: unexpected content-type {content_type!r}"
        )
    body = response.text
    locs = extract_sitemap_locs(body)
    if locs != EXPECTED_SITEMAP_LOCS:
        raise AssertionError(
            f"{label} /sitemap.xml: expected {EXPECTED_SITEMAP_LOCS!r}, "
            f"got {locs!r}"
        )
    for hint in FORBIDDEN_SITEMAP_HINTS:
        if hint in body:
            raise AssertionError(
                f"{label} /sitemap.xml: forbidden token {hint!r} appeared "
                f"in sitemap body"
            )
    if "<urlset" not in body or "</urlset>" not in body:
        raise AssertionError(
            f"{label} /sitemap.xml: missing <urlset> root element"
        )
    print(f"[PASS] {label} /sitemap.xml -> {content_type} ({len(locs)} urls)")


def verify_mode(label: str, root_path: str | None) -> None:
    with configured_root_path(root_path):
        client = build_client(root_path)
        verify_robots(client, label)
        verify_sitemap(client, label)


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("All robots/sitemap checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
