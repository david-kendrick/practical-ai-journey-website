"""Crawlability endpoints for the Practical AI Journey FastAPI app.

Provides:

* ``GET /robots.txt`` — crawl-allowed response pointing crawlers at the
  canonical sitemap.
* ``GET /sitemap.xml`` — sitemap listing every public, indexable page at
  its apex-domain canonical URL. Local preview URLs, ``www`` aliases,
  extensionless route aliases, and the operational
  ``/projects/practical-ai-journey/`` subpath fallback are deliberately
  omitted so the sitemap only advertises URLs we want indexed.

The canonical domain is shared with ``app.routes.pages`` so both
``<link rel="canonical">`` and ``<loc>`` entries stay in lock-step.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

# Reuse the same apex-domain constant the page router uses for canonical
# tags. Importing (rather than redeclaring) keeps canonical links, the
# sitemap, and robots.txt pointed at the same host.
from app.routes.pages import CANONICAL_DOMAIN

router = APIRouter(tags=["seo"])

# Apex-domain canonical URLs for every public, indexable page. Order is
# intentional: homepage first, then the case-study pages, then the
# meta/workflow pages. Edit this list (and only this list) to register a
# new public URL with crawlers.
SITEMAP_URLS: tuple[str, ...] = (
    f"{CANONICAL_DOMAIN}/",
    f"{CANONICAL_DOMAIN}/manitoba-cottage-search.html",
    f"{CANONICAL_DOMAIN}/student-assignment-tracker.html",
    f"{CANONICAL_DOMAIN}/hermes-workflow.html",
    f"{CANONICAL_DOMAIN}/local-models-benchmarking.html",
)

ROBOTS_BODY = (
    "User-agent: *\n"
    "Allow: /\n"
    "\n"
    f"Sitemap: {CANONICAL_DOMAIN}/sitemap.xml\n"
)


def render_sitemap_xml() -> str:
    """Render the sitemap document from :data:`SITEMAP_URLS`.

    Kept as a small function so tests can exercise the exact byte output
    without spinning up the full FastAPI app.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in SITEMAP_URLS:
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")  # trailing newline keeps the body POSIX-friendly
    return "\n".join(lines)


@router.get("/robots.txt", include_in_schema=False)
def robots() -> PlainTextResponse:
    """Serve a crawl-allowed ``robots.txt`` with the sitemap pointer."""
    return PlainTextResponse(
        content=ROBOTS_BODY,
        media_type="text/plain; charset=utf-8",
    )


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    """Serve the XML sitemap of canonical public URLs."""
    return Response(
        content=render_sitemap_xml(),
        media_type="application/xml; charset=utf-8",
    )


__all__ = [
    "router",
    "robots",
    "sitemap",
    "render_sitemap_xml",
    "SITEMAP_URLS",
    "ROBOTS_BODY",
]
