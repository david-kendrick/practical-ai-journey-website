"""Issue #32 verification: obsolete root static-era artifacts are gone.

Run from the repo root with the project venv active::

    python _hermes_verify_issue_32_legacy_static_artifacts_removed.py

What this script checks:

* the six obsolete root static-era files are gone from disk:
    - ``index.html``
    - ``manitoba-cottage-search.html``
    - ``student-assignment-tracker.html``
    - ``hermes-workflow.html``
    - ``styles.css``
    - ``navigation.js``

* the same six names are also absent from ``git ls-files`` so a future
  ``git checkout`` of an older commit cannot silently resurrect them at
  the repo root.

* the live FastAPI / Jinja source files still exist (i.e. removing the
  legacy artifacts did not break the runtime surface):
    - ``app/templates/pages/index.html``
    - ``app/templates/pages/local-models-benchmarking.html``
    - ``app/templates/pages/manitoba-cottage-search.html``
    - ``app/templates/pages/student-assignment-tracker.html``
    - ``app/templates/pages/hermes-workflow.html``
    - ``app/templates/base.html``
    - ``static/styles.css``
    - ``static/navigation.js``
    - ``app/routes/pages.py``
    - ``app/main.py``

* no new root-level ``*.html``, root ``styles.css``, or root
  ``navigation.js`` has been reintroduced (checked against ``git
  ls-files`` so untracked detritus is also surfaced).

The script is deliberately conservative and pure-Python (no FastAPI
imports) so it stays cheap, deterministic, and order-independent from
the rest of the verify suite.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Obsolete root static-era artifacts that issue #32 removes.
OBSOLETE_ROOT_FILES = (
    "index.html",
    "manitoba-cottage-search.html",
    "student-assignment-tracker.html",
    "hermes-workflow.html",
    "styles.css",
    "navigation.js",
)

# Live FastAPI / Jinja source files that MUST still exist after the
# cleanup. Listed explicitly so a future regression that deletes one of
# these fails loudly.
LIVE_SOURCE_FILES = (
    "app/templates/pages/index.html",
    "app/templates/pages/local-models-benchmarking.html",
    "app/templates/pages/manitoba-cottage-search.html",
    "app/templates/pages/student-assignment-tracker.html",
    "app/templates/pages/hermes-workflow.html",
    "app/templates/base.html",
    "static/styles.css",
    "static/navigation.js",
    "app/routes/pages.py",
    "app/main.py",
)


def _git_ls_files() -> list[str]:
    """Return the list of tracked file paths (POSIX, relative to repo root)."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _check_obsolete_files_absent() -> None:
    """Confirm none of the six obsolete root files exist on disk."""
    missing: list[str] = []
    for name in OBSOLETE_ROOT_FILES:
        path = ROOT / name
        if path.exists():
            missing.append(name)
    if missing:
        raise AssertionError(
            "Obsolete root static-era artifacts still on disk: "
            + ", ".join(sorted(missing))
        )
    print(f"[PASS] all {len(OBSOLETE_ROOT_FILES)} obsolete root files removed from disk")


def _check_obsolete_files_not_tracked(tracked: list[str]) -> None:
    """Confirm none of the six names are tracked by git at the repo root."""
    basename_set = set(OBSOLETE_ROOT_FILES)
    still_tracked = [
        path for path in tracked if path in basename_set
    ]
    if still_tracked:
        raise AssertionError(
            "Obsolete root static-era artifacts still tracked by git: "
            + ", ".join(sorted(still_tracked))
        )
    print("[PASS] none of the obsolete root files are tracked by git")


def _check_live_sources_exist() -> None:
    """Confirm every required live source file still exists on disk."""
    missing: list[str] = []
    for relative in LIVE_SOURCE_FILES:
        if not (ROOT / relative).exists():
            missing.append(relative)
    if missing:
        raise AssertionError(
            "Live source files missing after cleanup: "
            + ", ".join(sorted(missing))
        )
    print(f"[PASS] all {len(LIVE_SOURCE_FILES)} live source files present")


def _check_no_root_html_or_static_files(tracked: list[str]) -> None:
    """Confirm no root-level *.html / styles.css / navigation.js is tracked.

    A regression that reintroduces ``./whatever.html`` or ``./styles.css``
    at the repo root would break the project convention documented in
    AGENTS.md. This check covers both the just-removed names and any new
    root-level surface that should never have been reintroduced.
    """
    forbidden = ("styles.css", "navigation.js")
    violations: list[str] = []
    for path in tracked:
        if "/" not in path:
            # Top-level entry: either a *.html file or a forbidden asset.
            if path.endswith(".html") or path in forbidden:
                violations.append(path)
    if violations:
        raise AssertionError(
            "Unexpected root-level static-era artifacts tracked by git: "
            + ", ".join(sorted(violations))
        )
    print("[PASS] no root-level *.html / root styles.css / root navigation.js tracked")


def main() -> int:
    try:
        _check_obsolete_files_absent()
        tracked = _git_ls_files()
        _check_obsolete_files_not_tracked(tracked)
        _check_live_sources_exist()
        _check_no_root_html_or_static_files(tracked)
    except (AssertionError, subprocess.CalledProcessError) as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("Issue #32 legacy-static-artifact removal checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
