"""Issue #31 verification: internal homepage links point at the canonical
homepage path (``/``) rather than ``index.html*``, in both root and
``/projects/practical-ai-journey`` subpath modes.

Run from the repo root with the project venv active::

    python _hermes_verify_issue_31_canonical_home_links.py

What this script checks:

* header brand link href is ``/`` (root mode) or
  ``/projects/practical-ai-journey/`` (subpath mode), with no fragment and
  never ``index.html``.
* footer ``Home`` link href ends with ``/`` (root) or
  ``/projects/practical-ai-journey/`` (subpath), never ``index.html``.
* each case-study "Back to examples" link href ends with ``/#examples``
  (root) or ``/projects/practical-ai-journey/#examples`` (subpath), never
  ``index.html#examples``.
* every link that points at the canonical homepage also returns HTTP 200
  when fetched, confirming the URL is actually wired up to the FastAPI
  router under both modes.

The script is deliberately conservative: any link that points at
``index.html*`` instead of the canonical homepage path fails loudly so
the issue's "no regression on internal navigation" acceptance criterion
cannot silently drift.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from os import environ

from fastapi.testclient import TestClient

ROOT_PATH = "/projects/practical-ai-journey"

# Routes that carry a "Back to examples" hero action.
CASE_STUDY_ROUTES = [
    "/manitoba-cottage-search.html",
    "/manitoba-cottage-search",
    "/student-assignment-tracker.html",
    "/student-assignment-tracker",
    "/hermes-workflow.html",
    "/hermes-workflow",
    "/local-models-benchmarking.html",
    "/local-models-benchmarking",
]

# Every public page; used to verify the brand + footer links render
# consistently from each.
PUBLIC_ROUTES = [
    "/",
    "/index.html",
    *CASE_STUDY_ROUTES,
]


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


def _build_client(root_path: str | None) -> TestClient:
    # Clear cached app modules between modes so Starlette URL generation
    # does not retain root_path state from the previous configuration.
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    from app.main import create_app

    if root_path:
        return TestClient(create_app(), root_path=root_path)
    return TestClient(create_app())


_BRAND_RE = re.compile(
    r'href="([^"]+)"[^>]*aria-label="David Kendrick portfolio home"',
)
_FOOTER_HOME_RE = re.compile(
    r'<nav class="footer-nav"[^>]*>.*?<a href="([^"]+)">Home</a>',
    re.DOTALL,
)
_BACK_EXAMPLES_RE = re.compile(
    r'href="([^"]*#examples)"[^>]*>\s*Back to examples',
)


def _expected_home_prefix(root_path: str | None) -> str:
    """Return the expected URL prefix the canonical homepage resolves to.

    In root mode this is empty (the homepage is ``/``). In subpath mode
    the FastAPI ``root_path`` is prepended so the URL stays valid.
    """
    return f"{root_path}/" if root_path else "/"


def _forbid_index_html(href: str, label: str, root_path: str | None) -> None:
    """Reject any href that still points at ``index.html*`` (the issue's
    explicit failure mode)."""
    if "index.html" in href:
        raise AssertionError(
            f"{label}: link still points at index.html: {href!r} "
            f"(root_path={root_path!r})"
        )


def _verify_brand_and_footer(
    client: TestClient,
    route: str,
    root_path: str | None,
) -> None:
    body = client.get(route).text
    expected_prefix = _expected_home_prefix(root_path)

    brand_match = _BRAND_RE.search(body)
    if not brand_match:
        raise AssertionError(f"{route}: brand link not found")
    brand_href = brand_match.group(1)
    _forbid_index_html(brand_href, f"{route} brand", root_path)
    if brand_href != expected_prefix:
        raise AssertionError(
            f"{route}: brand href should be {expected_prefix!r} "
            f"but got {brand_href!r}"
        )
    print(f"[PASS] {route} brand={brand_href}")

    footer_match = _FOOTER_HOME_RE.search(body)
    if not footer_match:
        raise AssertionError(f"{route}: footer Home link not found")
    footer_href = footer_match.group(1)
    _forbid_index_html(footer_href, f"{route} footer", root_path)
    if footer_href != expected_prefix and footer_href != expected_prefix.rstrip("/"):
        raise AssertionError(
            f"{route}: footer Home href should be {expected_prefix!r} "
            f"but got {footer_href!r}"
        )
    print(f"[PASS] {route} footer_home={footer_href}")


def _verify_back_to_examples(
    client: TestClient,
    route: str,
    root_path: str | None,
) -> None:
    body = client.get(route).text
    expected_prefix = _expected_home_prefix(root_path)
    match = _BACK_EXAMPLES_RE.search(body)
    if not match:
        raise AssertionError(f"{route}: Back-to-examples link not found")
    href = match.group(1)
    _forbid_index_html(href, f"{route} back-to-examples", root_path)
    expected = f"{expected_prefix}#examples"
    if href != expected:
        raise AssertionError(
            f"{route}: back-to-examples href should be {expected!r} "
            f"but got {href!r}"
        )
    print(f"[PASS] {route} back-to-examples={href}")


def _verify_links_resolve(client: TestClient, root_path: str | None) -> None:
    """Confirm the homepage URL referenced by every link is reachable.

    Strips the ``#anchor`` fragment before fetching so FastAPI treats it
    as a normal GET against the homepage route.
    """
    for route in PUBLIC_ROUTES:
        body = client.get(route).text
        # Brand and footer point at the homepage; verify both are reachable.
        for fragment_re, label in (
            (_BRAND_RE, "brand"),
            (_FOOTER_HOME_RE, "footer"),
        ):
            match = fragment_re.search(body)
            if match is None:
                continue
            target = match.group(1).split("#", 1)[0]
            if not target:
                target = "/"
            response = client.get(target)
            if response.status_code != 200:
                raise AssertionError(
                    f"{route}: {label} link target {target!r} returned "
                    f"{response.status_code}"
                )
        # Case-study pages also carry the back-to-examples link.
        if route in CASE_STUDY_ROUTES:
            match = _BACK_EXAMPLES_RE.search(body)
            if match is not None:
                target = match.group(1).split("#", 1)[0]
                if not target:
                    target = "/"
                response = client.get(target)
                if response.status_code != 200:
                    raise AssertionError(
                        f"{route}: back-to-examples target {target!r} "
                        f"returned {response.status_code}"
                    )
    print(f"[PASS] all homepage link targets resolve (root_path={root_path!r})")


def verify_mode(label: str, root_path: str | None) -> None:
    with configured_root_path(root_path):
        client = _build_client(root_path)
        for route in PUBLIC_ROUTES:
            _verify_brand_and_footer(client, route, root_path)
        for route in CASE_STUDY_ROUTES:
            _verify_back_to_examples(client, route, root_path)
        _verify_links_resolve(client, root_path)
        print(f"[PASS] {label}: all canonical-homepage link checks passed")


def main() -> int:
    try:
        verify_mode("root", None)
        verify_mode("subpath", ROOT_PATH)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("All issue #31 canonical-homepage-link checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())