# Practical AI Journey agent instructions

This project is a FastAPI/Jinja site, not a root-level static HTML site.

Runtime source of truth:
- Page templates: `app/templates/pages/*.html`
- Shared layout/partials: `app/templates/base.html`, `app/templates/partials/*.html`
- Live assets: `static/styles.css`, `static/navigation.js`
- Routes: `app/routes/pages.py`
- App entrypoint: `app/main.py`

Archived/removed static-era artifacts:
- root `index.html`
- root `manitoba-cottage-search.html`
- root `student-assignment-tracker.html`
- root `hermes-workflow.html`
- root `styles.css`
- root `navigation.js`

Do not create new root-level `.html`, root `styles.css`, or root `navigation.js` files for site updates. If you think a root static file must return, stop and explain why first.

The custom domain cutover is complete. The canonical public URL is `https://davidkendrick.dev/`; `www` redirects to the apex. Treat `/projects/practical-ai-journey/` as an operational fallback only, not the public surface.

For visual/content updates, edit the Jinja templates and `static/` assets, then verify with the FastAPI app or `_hermes_verify_site.py`.

Local run command:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 4173
```
