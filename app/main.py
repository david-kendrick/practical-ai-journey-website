"""FastAPI app for the Practical AI Journey website.

Page content is migrating from the static root HTML files onto Jinja2
templates under ``app/templates/``. The homepage is the first migrated
page and is served by ``app.routes.pages`` at both ``/`` and
``/index.html`` so existing ``*.html`` nav hrefs keep working. All public
portfolio pages now render through FastAPI/Jinja, while root-level static
HTML files remain in the repo as rollback/reference artifacts during the
deployment-shape migration.

Runtime mount configuration:
- set ``PRACTICAL_AI_ROOT_PATH=/projects/practical-ai-journey`` when the app
  is reverse-proxied under that VPS subpath
- nginx should strip the public prefix before proxying and forward
  ``X-Script-Name`` with the same mount path

Run locally with::

    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import pages

# Project root is two levels up from this file (app/main.py). The static/
# directory at the repo root holds the working copies of styles.css and
# navigation.js; root-level styles.css/navigation.js and the root HTML
# pages are left untouched and stay the live static site.
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
    )

    # Mount the static asset directory so Jinja templates can use
    # url_for('static', path='styles.css') / 'navigation.js'. The directory
    # exists from the scaffold slice; if missing, skip mounting rather than
    # fail import so the app is still usable in stripped-down envs.
    if _STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

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
    return app


app = create_app()


__all__ = ["app", "create_app"]
