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
# share one context so they cannot drift apart.
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


# Student Assignment Tracker case-study page. Served at both
# ``/student-assignment-tracker.html`` (primary, matching the existing
# ``*.html`` nav hrefs used across the site) and the extensionless
# ``/student-assignment-tracker`` alias allowed by the migration plan.
# Both routes share one context so they cannot drift apart.
STUDENT_ASSIGNMENT_TRACKER_CONTEXT = {
    "title": "Student Assignment Tracker",
    "description": (
        "Case study for a Student Assignment Tracker: an education tracker "
        "built with FastAPI, SQLite, HTMX, and an agent-assisted development "
        "workflow."
    ),
    "active_page": "student-assignment-tracker",
    "page_aria_label": "Student Assignment Tracker sections",
    "page_sections": [
        {"href": "#problem", "label": "Problem"},
        {"href": "#build", "label": "Build"},
        {"href": "#ai-workflow", "label": "AI workflow"},
        {"href": "#agent-api", "label": "Agent API"},
        {"href": "#takeaways", "label": "Takeaways"},
    ],
}


def _render_student_assignment_tracker(request: Request) -> HTMLResponse:
    """Render the Student Assignment Tracker template with the shared context."""
    return templates.TemplateResponse(
        request,
        "pages/student-assignment-tracker.html",
        STUDENT_ASSIGNMENT_TRACKER_CONTEXT,
    )


@router.get("/student-assignment-tracker.html", include_in_schema=True)
def studentAssignmentTracker(request: Request) -> HTMLResponse:
    """Primary Student Assignment Tracker case-study route (``*.html`` form)."""
    return _render_student_assignment_tracker(request)


@router.get("/student-assignment-tracker", include_in_schema=False)
def studentAssignmentTrackerCompat(request: Request) -> HTMLResponse:
    """Extensionless alias allowed by the migration plan.

    Renders the exact same template/context as
    ``/student-assignment-tracker.html`` so the two routes produce identical
    HTML.
    """
    return _render_student_assignment_tracker(request)


# Hermes Workflow case-study page. Served at both ``/hermes-workflow.html``
# (primary, matching the existing ``*.html`` nav hrefs used across the site)
# and the extensionless ``/hermes-workflow`` alias allowed by the migration
# plan. Both routes share one context so they cannot drift apart.
HERMES_WORKFLOW_CONTEXT = {
    "title": "How I Structured My AI Agent Workflow",
    "description": (
        "Agent workflow page describing how David Kendrick uses Hermes "
        "profiles, memory, skills, model routing, and review gates to "
        "structure practical AI work."
    ),
    "active_page": "hermes-workflow",
    "page_aria_label": "Agent Workflow sections",
    "page_sections": [
        {"href": "#profiles", "label": "Profiles"},
        {"href": "#memory-skills", "label": "Memory & skills"},
        {"href": "#routing", "label": "Routing"},
        {"href": "#takeaways", "label": "Takeaways"},
    ],
}


LOCAL_MODELS_BENCHMARKING_CONTEXT = {
    "title": "Local Models and Benchmarking on Atlas",
    "description": (
        "Local models page describing David Kendrick's Atlas Mac Mini M4 "
        "experiments with Ollama, MLX, oMLX, and a repeatable coding benchmark "
        "for speed, reliability, and memory-ceiling tradeoffs."
    ),
    "active_page": "local-models-benchmarking",
    "page_aria_label": "Local Models and Benchmarking sections",
    "page_sections": [
        {"href": "#problem", "label": "Why"},
        {"href": "#atlas-setup", "label": "Atlas setup"},
        {"href": "#benchmark-results", "label": "Results"},
        {"href": "#constraints", "label": "Lessons"},
        {"href": "#takeaways", "label": "Takeaways"},
    ],
}


def _render_hermes_workflow(request: Request) -> HTMLResponse:
    """Render the Hermes Workflow template with the shared context."""
    return templates.TemplateResponse(
        request,
        "pages/hermes-workflow.html",
        HERMES_WORKFLOW_CONTEXT,
    )


@router.get("/hermes-workflow.html", include_in_schema=True)
def hermesWorkflow(request: Request) -> HTMLResponse:
    """Primary Hermes Workflow case-study route (``*.html`` form)."""
    return _render_hermes_workflow(request)


@router.get("/hermes-workflow", include_in_schema=False)
def hermesWorkflowCompat(request: Request) -> HTMLResponse:
    """Extensionless alias allowed by the migration plan.

    Renders the exact same template/context as ``/hermes-workflow.html`` so
    the two routes produce identical HTML.
    """
    return _render_hermes_workflow(request)


def _render_local_models_benchmarking(request: Request) -> HTMLResponse:
    """Render the Local Models and Benchmarking template with shared context."""
    return templates.TemplateResponse(
        request,
        "pages/local-models-benchmarking.html",
        LOCAL_MODELS_BENCHMARKING_CONTEXT,
    )


@router.get("/local-models-benchmarking.html", include_in_schema=True)
def localModelsBenchmarking(request: Request) -> HTMLResponse:
    """Primary Local Models and Benchmarking route (``*.html`` form)."""
    return _render_local_models_benchmarking(request)


@router.get("/local-models-benchmarking", include_in_schema=False)
def localModelsBenchmarkingCompat(request: Request) -> HTMLResponse:
    """Extensionless alias allowed by the migration plan.

    Renders the exact same template/context as
    ``/local-models-benchmarking.html`` so the two routes produce identical
    HTML.
    """
    return _render_local_models_benchmarking(request)

