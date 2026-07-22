"""Acceptance smoke checks for the Local Models and Benchmarking page.

Run from the repository root::

    python _hermes_verify_local_models_benchmarking_page.py

Verifies both route forms, the shared page shell, current benchmark evidence,
section navigation, and removal of superseded benchmark claims.
"""

from __future__ import annotations

import sys

from fastapi.testclient import TestClient

from app.main import app


ROUTES = ["/local-models-benchmarking.html", "/local-models-benchmarking"]

REQUIRED_TEXT = [
    "What I learned running local models on a Mac Mini",
    "Qwen3.6-35B-A3B-RotorQuant-MLX-3bit",
    "4/4 tests",
    "72.33s",
    "Qwen3.5-9B-Fable-5-v1-oQ8",
    "1/4 tests in 220.39s",
    "Ternary-Bonsai-27B-mlx-2bit",
    "1/4 tests",
    "167.67s",
    "Bonsai was stronger for chat, but not for coding",
    "88.26s",
    "8.92GB",
    "both math problems correct",
    "99.34s",
    "7.03GB",
    "11.2% faster than Gemma",
    "2,200-token limit",
    "Verify the effective ceiling",
    "roughly 21GiB",
    'href="#benchmark-results"',
    'href="#chat-reasoning"',
    'href="#constraints"',
]

SUPERSEDED_TEXT = [
    "Fastest strong run I observed",
    "Could not be benchmarked fairly under the current Mac Mini Metal memory ceiling",
    "The fastest result was not automatically the best result",
    "A useful language model was not automatically a reliable reasoner",
    "12.7 output tokens per second",
    "48 legs, not 38",
]

SHARED_SHELL_MARKERS = [
    '<nav class="nav-row primary-nav"',
    '<nav class="nav-row secondary-nav"',
    '<footer class="site-footer">',
    "David Kendrick portfolio home",
]

STATIC_MARKERS = ["/static/styles.css", "/static/navigation.js"]


def main() -> int:
    client = TestClient(app)
    bodies: dict[str, str] = {}

    stylesheet = client.get("/static/styles.css")
    if stylesheet.status_code != 200:
        print(f"[FAIL] stylesheet: expected 200, got {stylesheet.status_code}")
        return 1
    if ".decision-step { align-self: start;" not in stylesheet.text:
        print("[FAIL] stylesheet: decision-step badges can stretch in grid rows")
        return 1
    print("[PASS] stylesheet: decision-step badges keep intrinsic height")

    for route in ROUTES:
        response = client.get(route)
        if response.status_code != 200:
            print(f"[FAIL] {route}: expected 200, got {response.status_code}")
            return 1

        body = response.text
        bodies[route] = body

        for marker in REQUIRED_TEXT + STATIC_MARKERS:
            if marker not in body:
                print(f"[FAIL] {route}: missing {marker!r}")
                return 1

        for stale_text in SUPERSEDED_TEXT:
            if stale_text in body:
                print(f"[FAIL] {route}: superseded copy remains: {stale_text!r}")
                return 1

        for marker in SHARED_SHELL_MARKERS:
            count = body.count(marker)
            if count != 1:
                print(
                    f"[FAIL] {route}: shared marker {marker!r} "
                    f"expected count 1, got {count}"
                )
                return 1

        if body.count('<main id="main"') != 1:
            print(f"[FAIL] {route}: expected exactly one main element")
            return 1

        print(f"[PASS] {route}: current benchmark markers present")

    primary, alias = ROUTES
    if bodies[primary] != bodies[alias]:
        print(f"[FAIL] {primary!r} and {alias!r} rendered different HTML")
        return 1

    print(f"[PASS] {primary!r} and {alias!r} render identical HTML")
    print("All Local Models and Benchmarking checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
