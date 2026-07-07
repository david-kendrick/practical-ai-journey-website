"""Focused FastAPI TestClient sanity script for the homepage hero CTA cluster.

Run from the repo root with the project venv active::

    python _hermes_verify_hero_ctas.py

The script mounts the FastAPI app, GETs ``/`` and ``/index.html``, and
asserts on the four hrefs defined by the issue #14 hero CTA cluster spec at
``app/templates/pages/index.html`` (lines 12-21):

  Primary CTAs (tier 1, ``.hero-primary-actions``):
    - href="#examples"
    - href="#next"
  Supporting page links (tier 2, ``.hero-secondary-links``):
    - href="hermes-workflow.html"
    - href="local-models-benchmarking.html"

Each route is asserted on three properties:
  1. response status 200
  2. all four hrefs are present in the rendered HTML
  3. the response was produced without a template rendering exception
     (a 500 or an HTMLResponse containing an exception traceback would fail)

The script exercises both deployment modes used elsewhere in the project:
  - root (no ``PRACTICAL_AI_ROOT_PATH``)
  - subpath (``/projects/practical-ai-journey``)

Run with no flags for the default behavior. Exit code 0 means all
assertions passed; non-zero means at least one assertion failed.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from os import environ

from fastapi.testclient import TestClient

ROOT_PATH = "/projects/practical-ai-journey"

ROUTES = ("/", "/index.html")

# The four hrefs from the issue #14 hero CTA cluster spec.
PRIMARY_CTA_HREFS = ("#examples", "#next")
SUPPORTING_PAGE_LINK_HREFS = (
    "hermes-workflow.html",
    "local-models-benchmarking.html",
)
EXPECTED_HREFS = PRIMARY_CTA_HREFS + SUPPORTING_PAGE_LINK_HREFS

# Heuristic markers that indicate Jinja raised an exception while rendering
# the template. Starlette returns 500 with a traceback page when a template
# raises; we double-check the body too in case of a swallowed exception.
RENDER_EXCEPTION_MARKERS = (
    "jinja2.exceptions",
    "TemplateSyntaxError",
    "UndefinedError",
    "Traceback (most recent call last)",
)


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
    # Clear app modules between modes because Starlette/Jinja URL generation
    # can otherwise retain state from the previous root_path configuration
    # inside this one process. Mirrors _hermes_verify_site.py.
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    from app.main import create_app

    if root_path:
        return TestClient(create_app(), root_path=root_path)
    return TestClient(create_app())


def assert_route(client: TestClient, route: str, label: str) -> None:
    # 1. status 200
    response = client.get(route)
    if response.status_code != 200:
        raise AssertionError(
            f"{label} {route}: expected 200, got {response.status_code}"
        )

    body = response.text

    # 2. all four hrefs present
    for href in EXPECTED_HREFS:
        if f'href="{href}"' not in body:
            raise AssertionError(
                f"{label} {route}: missing href=\"{href}\""
            )

    # 3. no template rendering exceptions surfaced in the body
    lowered = body.lower()
    for marker in RENDER_EXCEPTION_MARKERS:
        if marker.lower() in lowered:
            raise AssertionError(
                f"{label} {route}: template rendering exception marker {marker!r}"
            )

    print(
        f"[PASS] {label} {route} 200, "
        f"all 4 hrefs present, no render exceptions"
    )


def verify_mode(label: str, root_path: str | None) -> None:
    with configured_root_path(root_path):
        client = build_client(root_path)
        for route in ROUTES:
            assert_route(client, route, label)


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("All hero CTA sanity checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())