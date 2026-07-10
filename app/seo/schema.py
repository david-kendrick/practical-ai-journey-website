"""JSON-LD structured-data builders for the Practical AI Journey site.

Centralizes the schema.org payloads so every page renders conservative,
factual structured data derived from the route context (titles,
descriptions, canonical URLs), not from invented credentials or third-party
claims.

Two shapes are exposed:

* :func:`build_homepage_graph` — a single ``@graph`` containing
  :class:`schema:Person` for David Kendrick and :class:`schema:WebSite` for
  the site, suitable for the homepage ``<script type="application/ld+json">``.

* :func:`build_page_document` — a single ``CreativeWork`` (or
  ``Article`` when ``og_type == "article"``) describing a secondary page,
  with an ``author`` reference to the same ``Person``.

The output is plain ``dict`` data so Jinja's ``tojson`` filter can serialize
it safely — no hand-built JSON strings, no HTML interpolation risks, and no
inline-JSON escaping pitfalls.

Constraints honored here:

* Public canonical URLs only (``https://davidkendrick.dev/...``). No
  ``www``, no ``/projects/practical-ai-journey/`` subpath fallback, no
  local preview origins.
* No invented credentials, employers, organizations, dates, ratings,
  reviews, offers, logos, or images.
* No ``BreadcrumbList`` per issue #29 spec.
"""

from __future__ import annotations

# Strict imports: keep this module dependency-free so it can be exercised
# directly from the verify scripts without spinning up FastAPI.
CANONICAL_DOMAIN = "https://davidkendrick.dev"

# Single source of truth for the Person used as both author and (where
# applicable) WebSite.publisher. Pulled out as a module constant so the
# homepage graph and the per-page CreativeWork payloads reference the
# exact same Person dictionary — required for schema.org @id reuse when
# we later decide to add @id fields, and useful right now to keep the
# preview readable.
PERSON = {
    "@type": "Person",
    "name": "David Kendrick",
    "url": f"{CANONICAL_DOMAIN}/",
    "description": (
        "Software engineer building practical AI systems: agents, "
        "workflows, local-model experiments, and browser automation."
    ),
}

# Conservative ``knowsAbout`` list for the homepage graph. Each value is
# derived from a visible, public topic across the site's case studies
# (Manitoba Cottage Search, Student Assignment Tracker, Hermes Workflow,
# Local Models / Benchmarking) — never from credentials, employers, or
# third-party claims.
PERSON_KNOWS_ABOUT: tuple[str, ...] = (
    "AI agents",
    "Agent workflows",
    "Local language models",
    "Browser automation",
    "FastAPI",
    "Knowledge bases",
)

# Stable @id-style identifier for the Person so the same Person object can
# be referenced by both the homepage WebSite.publisher and any
# CreativeWork.author on secondary pages without redefining fields.
PERSON_ID = f"{CANONICAL_DOMAIN}/#person"


def _person_payload() -> dict:
    """Return a Person payload with an ``@id`` for reuse across graphs."""
    return {
        **PERSON,
        "@id": PERSON_ID,
        "knowsAbout": list(PERSON_KNOWS_ABOUT),
    }


def build_homepage_graph() -> dict:
    """Build the homepage JSON-LD graph.

    Returns a single dict shaped like::

        {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "Person", ...},
                {"@type": "WebSite", ..., "publisher": {"@id": ...}},
            ],
        }

    WebSite.publisher references the Person by ``@id`` so the two nodes
    are explicitly linked without duplicating fields.
    """
    person = _person_payload()
    website = {
        "@type": "WebSite",
        "name": "David Kendrick",
        "url": f"{CANONICAL_DOMAIN}/",
        "description": (
            "Hands-on work by David Kendrick on practical AI systems: "
            "agents, workflow design, local model experiments, and browser "
            "automation."
        ),
        "publisher": {"@id": PERSON_ID},
        "inLanguage": "en",
    }
    return {
        "@context": "https://schema.org",
        "@graph": [person, website],
    }


def build_page_document(
    *,
    headline: str,
    description: str,
    url: str,
    og_type: str,
) -> dict:
    """Build a single schema.org node for a secondary page.

    ``headline`` and ``description`` come straight from the page's route
    context. ``url`` is the page's apex-domain canonical URL. ``og_type``
    switches the schema type:

    * ``"article"`` -> ``Article``
    * anything else -> ``CreativeWork``

    ``author`` references the shared Person by ``@id`` so each page's
    authorship traces back to one well-defined identity.
    """
    schema_type = "Article" if og_type == "article" else "CreativeWork"
    # Article keeps CreativeWork's field list (``name``/``description``)
    # untouched and adds ``headline`` for richer search-result rendering.
    # Non-article pages have no separate headline, so we fold the page
    # title into ``name`` only.
    payload: dict = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": headline,
        "description": description,
        "url": url,
        "author": {"@id": PERSON_ID},
        "inLanguage": "en",
    }
    if schema_type == "Article":
        payload["headline"] = headline
    return payload


__all__ = [
    "CANONICAL_DOMAIN",
    "PERSON",
    "PERSON_ID",
    "PERSON_KNOWS_ABOUT",
    "build_homepage_graph",
    "build_page_document",
]
