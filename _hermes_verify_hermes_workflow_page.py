"""Acceptance smoke checks for the Hermes Workflow page migration.

Run from the repo root with the venv active::

    python _hermes_verify_hermes_workflow_page.py

Verifies that ``/hermes-workflow.html`` and the extensionless
``/hermes-workflow`` alias both render through FastAPI/Jinja with HTTP 200,
that the two routes render identical HTML, that key page copy and section
anchors are present, that the shared header/footer partials are rendered (not
duplicated page-local markup), that static asset URLs point at ``/static/``,
and that exactly one ``<main id=\"main\">`` survives.
"""

from __future__ import annotations

import sys

from fastapi.testclient import TestClient

from app.main import app


REQUIRED_TEXT = [
    "How I structured my AI agent workflow",
    "Profiles turn AI work into assigned roles",
    "Making AI work durable instead of disposable",
    "The right lane depends on the job",
    "What this taught me",
    'href="#profiles"',
    'href="#memory-skills"',
    'href="#routing"',
    'href="#takeaways"',
]

SHARED_SHELL_MARKERS = [
    '<nav class="nav-row primary-nav"',
    '<nav class="nav-row secondary-nav"',
    '<footer class="site-footer">',
    "David Kendrick portfolio home",
]

STATIC_MARKERS = [
    "/static/styles.css",
    "/static/navigation.js",
]

ROUTES = ["/hermes-workflow.html", "/hermes-workflow"]


def _assert_present(body: str, needle: str) -> None:
    if needle not in body:
        raise AssertionError(f"missing in response body: {needle!r}")


def main() -> int:
    client = TestClient(app)

    bodies = {}

    for route in ROUTES:
        try:
            response = client.get(route)
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"[FAIL] {route}: request raised {exc!r}")
            return 1
        if response.status_code != 200:
            print(f"[FAIL] {route}: expected 200, got {response.status_code}")
            print(response.text[:500])
            return 1
        body = response.text
        bodies[route] = body
        for needle in REQUIRED_TEXT:
            try:
                _assert_present(body, needle)
            except AssertionError as exc:
                print(f"[FAIL] {route}: {exc}")
                return 1
        for marker in SHARED_SHELL_MARKERS:
            count = body.count(marker)
            if count != 1:
                print(
                    f"[FAIL] {route}: shared marker {marker!r} "
                    f"expected count 1, got {count}"
                )
                return 1
        for marker in STATIC_MARKERS:
            try:
                _assert_present(body, marker)
            except AssertionError as exc:
                print(f"[FAIL] {route}: {exc}")
                return 1
        main_open = '<main id="main"'
        if body.count(main_open) != 1:
            print(
                f"[FAIL] {route}: expected exactly one "
                f'<main id="main">, got {body.count(main_open)}'
            )
            return 1
        print(f"[PASS] {route}: HTTP 200, all markers present")

    primary, alias = ROUTES
    if bodies[primary] != bodies[alias]:
        print(f"[FAIL] {primary!r} and {alias!r} rendered different HTML")
        return 1
    print(f"[PASS] {primary!r} and {alias!r} render identical HTML")

    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
