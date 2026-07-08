# Practical AI Journey Website

FastAPI/Jinja portfolio site for David Kendrick's Practical AI Journey pages.

Canonical live URL: `https://davidkendrick.dev/`

## Requirements

- Python `>=3.10`
- Python `3.12` recommended locally because the VPS runs Python `3.12.3`

The runtime/test-client dependency versions are pinned in `requirements.txt` so local verification matches the VPS dependency layer.

## Run the FastAPI app locally

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 4173
```

Open:

```text
http://127.0.0.1:4173/
```

FastAPI pages available locally:

- `http://127.0.0.1:4173/`
- `http://127.0.0.1:4173/index.html`
- `http://127.0.0.1:4173/manitoba-cottage-search.html`
- `http://127.0.0.1:4173/manitoba-cottage-search`
- `http://127.0.0.1:4173/student-assignment-tracker.html`
- `http://127.0.0.1:4173/student-assignment-tracker`
- `http://127.0.0.1:4173/hermes-workflow.html`
- `http://127.0.0.1:4173/hermes-workflow`
- `http://127.0.0.1:4173/local-models-benchmarking.html`
- `http://127.0.0.1:4173/local-models-benchmarking`
- `http://127.0.0.1:4173/healthz`

## Source of truth

The site is FastAPI/Jinja. Edit these files for site changes:

- page templates: `app/templates/pages/*.html`
- shared layout/partials: `app/templates/base.html`, `app/templates/partials/*.html`
- live assets: `static/styles.css`, `static/navigation.js`
- routes: `app/routes/pages.py`

Do not recreate root-level static HTML files, root `styles.css`, or root `navigation.js`. Those static-era artifacts were removed after the custom-domain cutover was completed.

## Local verification

Current smoke check:

```bash
python _hermes_verify_site.py
```

The smoke check verifies root mode, VPS subpath mode, public page routes, extensionless aliases, static assets, and `/healthz`.

## VPS deployment shape

Current canonical host:

```text
https://davidkendrick.dev/
```

VPS checkout:

```text
/var/www/projects/practical-ai-journey
```

The canonical domain-root app runs on loopback with no public root path:

```bash
PRACTICAL_AI_ROOT_PATH= python -m uvicorn app.main:app --host 127.0.0.1 --port 8011
```

Deployment templates:

- `deploy/practical-ai-journey-custom-domain.service`
- `deploy/nginx-practical-ai-journey-custom-domain.conf`

The old `/projects/practical-ai-journey/` subpath service/config may still exist as an operational fallback, but it is not the canonical public surface.

## Documentation

Project planning, deployment history, cutover records, and archived static-era notes live in Obsidian under:

```text
/Users/david/Obsidian Vault/Projects/Practical AI Journey Website/
```

## Source evidence

Draft copy is based on Obsidian notes, especially:

- `/Users/david/Obsidian Vault/Agent-Hermes/projects/ai-career-prep/project-evidence-review.md`
- `/Users/david/Obsidian Vault/Agent-Hermes/projects/ai-career-prep/practical-ai-journey-draft.md`
