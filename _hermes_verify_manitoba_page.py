"""Acceptance smoke checks for the Manitoba Cottage Search page migration.

Run from the repo root with the venv active::

    python _hermes_verify_manitoba_page.py

Verifies that ``/manitoba-cottage-search.html`` and the extensionless
``/manitoba-cottage-search`` alias both render through FastAPI/Jinja with
HTTP 200, that key page copy and section anchors are present, that the
shared header/footer partials are rendered (not duplicated page-local
markup), and that static asset URLs point at ``/static/``.
"""

from __future__ import annotations

import sys

from fastapi.testclient import TestClient

from app.main import app


REQUIRED_TEXT = [
    "Manitoba Cottage Search",
    "The data was stuck in a spreadsheet",
    "What exists now and how the pipeline is shaped",
    "AI role: discovery, scoring, and bounded automation",
    "What I learned",
    'href="#problem"',
    'href="#architecture"',
    'href="#ai-role"',
    'href="#lessons"',
]

# Shared-shell markers from the partials — proves the page uses base.html,
# not duplicated page-local header/footer markup.
SHARED_SHELL_MARKERS = [
    '<nav class="nav-row primary-nav"',
    '<nav class="nav-row secondary-nav"',
    '<footer class="site-footer">',
    "David Kendrick portfolio home",
]

# Static asset URLs must point at the mounted /static/ directory, not the
# root-relative bare filenames used by the unmigrated static pages.
# Starlette's url_for produces absolute URLs under TestClient
# (http://testserver/static/...), so match the path segment, which is stable
# across absolute and relative forms.
STATIC_MARKERS = [
    "/static/styles.css",
    "/static/navigation.js",
]

ROUTES = ["/manitoba-cottage-search.html", "/manitoba-cottage-search"]


def _assert_present(body: str, needle: str) -> None:
    if needle not in body:
        raise AssertionError(f"missing in response body: {needle!r}")


def main() -> int:
    client = TestClient(app)

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
        for needle in REQUIRED_TEXT:
            try:
                _assert_present(body, needle)
            except AssertionError as exc:
                print(f"[FAIL] {route}: {exc}")
                return 1
        # The shared shell should appear exactly once per page (header x1,
        # footer x1). If the page-local header/footer markup were pasted in,
        # these counts would be 2.
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
        # No duplicated <main> wrapper from the static source should survive.
        main_open = '<main id="main"'
        if body.count(main_open) != 1:
            print(
                f"[FAIL] {route}: expected exactly one "
                f"<main id=\"main\">, got {body.count(main_open)}"
            )
            return 1
        print(f"[PASS] {route}: HTTP 200, all markers present")

    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
