"""Pages router.

Renders Jinja2-backed pages for the Practical AI Journey site. The homepage
is the first migrated page and is served at both ``/`` and ``/index.html``
to preserve the existing ``*.html`` nav hrefs across sibling pages.

Per-page context is kept here so templates stay declarative and the
shared ``base.html`` / header / footer receive a stable contract.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Templates live alongside the app package so imports stay stable regardless
# of the current working directory (uvicorn, TestClient, ad-hoc shells).
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter(tags=["pages"])

# Shared homepage context. Kept in one place so / and /index.html cannot
# drift apart, and so future pages can mirror this pattern.
HOMEPAGE_CONTEXT = {
    "title": "Building Practical AI Systems",
    "description": (
        "A draft portfolio page describing David Kendrick's hands-on practical "
        "AI journey: agents, workflow design, local models, browser automation, "
        "and enterprise-ready lessons."
    ),
    "active_page": "index",
    "page_aria_label": "Main page sections",
    "page_sections": [
        {"href": "#journey", "label": "Journey"},
        {"href": "#examples", "label": "Examples"},
        {"href": "#lessons", "label": "Lessons"},
        {"href": "#next", "label": "Next"},
    ],
}


def _render_homepage(request: Request) -> HTMLResponse:
    """Render the homepage template with the shared context."""
    return templates.TemplateResponse(request, "pages/index.html", HOMEPAGE_CONTEXT)


@router.get("/", include_in_schema=True)
def home(request: Request) -> HTMLResponse:
    """Primary homepage route."""
    return _render_homepage(request)


@router.get("/index.html", include_in_schema=False)
def homeCompat(request: Request) -> HTMLResponse:
    """Compatibility alias so existing ``index.html`` nav hrefs resolve.

    Renders the exact same template/context as ``/`` so the two routes
    produce identical HTML; verified by the acceptance smoke checks.
    """
    return _render_homepage(request)


# Manitoba Cottage Search case-study page. Served at both
# ``/manitoba-cottage-search.html`` (primary, matching the existing ``*.html``
# nav hrefs used across the site) and the extensionless
# ``/manitoba-cottage-search`` alias allowed by the migration plan. Both routes
# share one context so they cannot drift apart; the root static
# ``manitoba-cottage-search.html`` remains untouched until replacement
# behavior is verified.
MANITOBA_COTTAGE_SEARCH_CONTEXT = {
    "title": "Manitoba Cottage Search",
    "description": (
        "Case study for Manitoba Cottage Search: a FastAPI and HTMX "
        "listing-review app with structured intake, browser-backed "
        "extraction, and agent-assisted workflow design."
    ),
    "active_page": "manitoba-cottage-search",
    "page_aria_label": "Manitoba Cottage Search sections",
    "page_sections": [
        {"href": "#problem", "label": "Problem"},
        {"href": "#architecture", "label": "Architecture"},
        {"href": "#ai-role", "label": "AI role"},
        {"href": "#lessons", "label": "Lessons"},
    ],
}


def _render_manitoba_cottage_search(request: Request) -> HTMLResponse:
    """Render the Manitoba Cottage Search template with the shared context."""
    return templates.TemplateResponse(
        request,
        "pages/manitoba-cottage-search.html",
        MANITOBA_COTTAGE_SEARCH_CONTEXT,
    )


@router.get("/manitoba-cottage-search.html", include_in_schema=True)
def manitobaCottageSearch(request: Request) -> HTMLResponse:
    """Primary Manitoba Cottage Search case-study route (``*.html`` form)."""
    return _render_manitoba_cottage_search(request)


@router.get("/manitoba-cottage-search", include_in_schema=False)
def manitobaCottageSearchCompat(request: Request) -> HTMLResponse:
    """Extensionless alias allowed by the migration plan.

    Renders the exact same template/context as ``/manitoba-cottage-search.html``
    so the two routes produce identical HTML.
    """
    return _render_manitoba_cottage_search(request)
