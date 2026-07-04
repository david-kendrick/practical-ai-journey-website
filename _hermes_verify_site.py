"""Full-site smoke checks for the Practical AI Journey FastAPI app.

Run from the repo root with the project venv active::

    python _hermes_verify_site.py

The script checks the root deployment mode and the current VPS subpath mode.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from os import environ

from fastapi.testclient import TestClient

ROOT_PATH = "/projects/practical-ai-journey"

ROOT_PATHS = [
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

STATIC_ROUTES = [
    "/static/styles.css",
    "/static/navigation.js",
]

EXPECTED_PAGE_MARKERS = {
    "/": ["Building Practical AI Systems"],
    "/index.html": ["Building Practical AI Systems"],
    "/manitoba-cottage-search.html": ["Manitoba Cottage Search"],
    "/manitoba-cottage-search": ["Manitoba Cottage Search"],
    "/student-assignment-tracker.html": ["Student Assignment Tracker"],
    "/student-assignment-tracker": ["Student Assignment Tracker"],
    "/hermes-workflow.html": ["How I Structured My AI Agent Workflow"],
    "/hermes-workflow": ["How I Structured My AI Agent Workflow"],
    "/local-models-benchmarking.html": ["What I learned running local models on Atlas"],
    "/local-models-benchmarking": ["What I learned running local models on Atlas"],
}


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


def assert_response(client: TestClient, route: str, expected_status: int = 200):
    response = client.get(route)
    if response.status_code != expected_status:
        raise AssertionError(
            f"{route}: expected {expected_status}, got {response.status_code}"
        )
    return response


def verify_mode(label: str, root_path: str | None) -> None:
    with configured_root_path(root_path):
        client = build_client(root_path)
        asset_prefix = root_path or ""
        expected_asset_markers = [
            f'{asset_prefix}/static/styles.css',
            f'{asset_prefix}/static/navigation.js',
        ]

        health = assert_response(client, "/healthz")
        payload = health.json()
        if payload.get("root_path") != (root_path or ""):
            raise AssertionError(
                f"{label}: health root_path mismatch: {payload.get('root_path')!r}"
            )
        print(f"[PASS] {label} /healthz")

        for route in ROOT_PATHS:
            response = assert_response(client, route)
            body = response.text
            for marker in EXPECTED_PAGE_MARKERS[route]:
                if marker not in body:
                    raise AssertionError(f"{label} {route}: missing marker {marker!r}")
            for marker in expected_asset_markers:
                if marker not in body:
                    raise AssertionError(
                        f"{label} {route}: missing asset marker {marker!r}"
                    )
            print(f"[PASS] {label} {route}")

        for route in STATIC_ROUTES:
            response = assert_response(client, route)
            content_type = response.headers.get("content-type", "")
            if route.endswith(".css") and "text/css" not in content_type:
                raise AssertionError(f"{label} {route}: unexpected {content_type!r}")
            if route.endswith(".js") and "javascript" not in content_type:
                raise AssertionError(f"{label} {route}: unexpected {content_type!r}")
            print(f"[PASS] {label} {route} {content_type}")


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("All site smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
