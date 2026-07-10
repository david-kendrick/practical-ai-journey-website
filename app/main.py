"""FastAPI app for the Practical AI Journey website.

Public pages render through Jinja2 templates under ``app/templates/`` and
are served by ``app.routes.pages``. ``*.html`` compatibility routes remain
for stable public URLs, but the old root-level static HTML/CSS/JS artifacts
were removed after the custom-domain cutover completed.

Runtime mount configuration:
- set ``PRACTICAL_AI_ROOT_PATH=/projects/practical-ai-journey`` when the app
  is reverse-proxied under that VPS subpath
- nginx should strip the public prefix before proxying and forward
  ``X-Script-Name`` with the same mount path

Run locally with::

    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    python -m uvicorn app.main:app --host 127.0.0.1 --port 4173
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.routes import pages, seo
from app.staticfiles import RootPathAwareStaticFiles

# Project root is two levels up from this file (app/main.py). The static/
# directory at the repo root holds the live FastAPI-served asset copies of
# styles.css and navigation.js. Root-level static-era HTML/CSS/JS artifacts
# were removed after the custom-domain cutover completed.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_STATIC_DIR = _PROJECT_ROOT / "static"


def create_app() -> FastAPI:
    """Application factory kept small so tests/import callers stay stable."""
    settings = get_settings()
    app = FastAPI(
        title="Practical AI Journey Website",
        description=(
            "FastAPI/Jinja2 site for the practical AI journey portfolio. "
            "All public case-study pages are Jinja-rendered and deployment can "
            "mount the app under /projects/practical-ai-journey via root_path."
        ),
        version="0.3.0",
        root_path=settings.root_path,
        root_path_in_servers=False,
    )

    # Mount the static asset directory so Jinja templates can use
    # url_for('static', path='styles.css') / 'navigation.js'. The directory
    # exists from the scaffold slice; if missing, skip mounting rather than
    # fail import so the app is still usable in stripped-down envs.
    if _STATIC_DIR.is_dir():
        app.mount(
            "/static",
            RootPathAwareStaticFiles(directory=str(_STATIC_DIR)),
            name="static",
        )

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> JSONResponse:
        return JSONResponse(
            {
                "ok": True,
                "app": "practical-ai-journey",
                "root_path": settings.root_path,
            }
        )

    app.include_router(pages.router)
    app.include_router(seo.router)
    return app


app = create_app()


__all__ = ["app", "create_app"]
