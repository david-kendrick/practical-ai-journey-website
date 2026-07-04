"""Regression checks for subpath-aware deployment behavior.

Run from the repo root with the venv active::

    python _hermes_verify_subpath_root_path.py

Verifies that the FastAPI app renders all migrated pages correctly when mounted
under ``/projects/practical-ai-journey`` and that generated asset URLs keep the
subpath prefix.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from os import environ

from fastapi.testclient import TestClient

ROOT_PATH = "/projects/practical-ai-journey"
ROUTES = [
    "/",
    "/index.html",
    "/manitoba-cottage-search.html",
    "/student-assignment-tracker.html",
    "/hermes-workflow.html",
]
ASSET_MARKERS = [
    f"{ROOT_PATH}/static/styles.css",
    f"{ROOT_PATH}/static/navigation.js",
]


@contextmanager
def temporary_root_path() -> Iterator[None]:
    previous = environ.get("PRACTICAL_AI_ROOT_PATH")
    environ["PRACTICAL_AI_ROOT_PATH"] = ROOT_PATH
    try:
        yield
    finally:
        if previous is None:
            environ.pop("PRACTICAL_AI_ROOT_PATH", None)
        else:
            environ["PRACTICAL_AI_ROOT_PATH"] = previous


def main() -> int:
    with temporary_root_path():
        from app.main import create_app

        client = TestClient(create_app(), root_path=ROOT_PATH)
        for route in ROUTES:
            response = client.get(route)
            if response.status_code != 200:
                print(f"[FAIL] {route}: expected 200, got {response.status_code}")
                return 1
            body = response.text
            for marker in ASSET_MARKERS:
                if marker not in body:
                    print(f"[FAIL] {route}: missing asset marker {marker!r}")
                    return 1
            print(f"[PASS] {route}: subpath assets preserved")

    print("All subpath checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
