"""Issue #27 smoke check: confirm the public-facing `draft` language is gone
from the live homepage while H1 and primary CTAs are preserved.

Runs the same dual-mode (root + /projects/practical-ai-journey) contract
the other Hermes verify scripts use.

Run from the repo root with the project venv active::

    python _hermes_verify_issue_27_draft_removed.py
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from os import environ

from fastapi.testclient import TestClient

ROOT_PATH = "/projects/practical-ai-journey"

ROOT_PATHS = ["/", "/index.html"]

PRIMARY_CTA_MARKERS = ("Review examples", "See professional direction")
H1_MARKER = "Building practical AI systems"

# Public-facing draft framings we must NOT see in the rendered homepage or its
# <meta name="description"> once issue #27 ships. The parent marketing-seo
# profile approved dropping both of these surfaces.
FORBIDDEN_PHRASES = (
    "Draft portfolio page",
    "A draft portfolio page",
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
    # Clear app modules so Starlette / Jinja re-read settings under the
    # current PRACTICAL_AI_ROOT_PATH (same pattern as _hermes_verify_site.py).
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
        for route in ROOT_PATHS:
            response = client.get(route)
            assert response.status_code == 200, (
                f"{label} {route}: expected 200, got {response.status_code}"
            )
            body = response.text

            for phrase in FORBIDDEN_PHRASES:
                assert phrase not in body, (
                    f"{label} {route}: forbidden draft phrase still present: {phrase!r}"
                )

            # Exactly one H1.
            h1_count = body.count("<h1")
            assert h1_count == 1, f"{label} {route}: expected 1 <h1>, got {h1_count}"
            assert H1_MARKER in body, f"{label} {route}: missing H1 text {H1_MARKER!r}"

            # Both primary CTAs must still render in the hero-actions block.
            for cta in PRIMARY_CTA_MARKERS:
                assert cta in body, f"{label} {route}: missing primary CTA {cta!r}"

            # Approved eyebrow should be on the live page now.
            assert "Practical AI" in body and "Systems builder" in body, (
                f"{label} {route}: new eyebrow not present"
            )

            print(f"[PASS] {label} {route}")


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("Issue #27 draft-removal checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
