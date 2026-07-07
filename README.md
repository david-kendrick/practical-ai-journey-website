# Practical AI Journey Draft

FastAPI/Jinja portfolio site for David Kendrick's Practical AI Journey pages.

## Requirements

- Python `>=3.10`
- Python `3.12` recommended locally because the VPS runs Python `3.12.3`

The runtime/test-client dependency versions are pinned in `requirements.txt` so local verification matches the VPS dependency layer.

## Run the FastAPI app locally

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Open:

```text
http://127.0.0.1:8001/
```

FastAPI pages available locally:

- `http://127.0.0.1:8001/`
- `http://127.0.0.1:8001/index.html`
- `http://127.0.0.1:8001/manitoba-cottage-search.html`
- `http://127.0.0.1:8001/manitoba-cottage-search`
- `http://127.0.0.1:8001/student-assignment-tracker.html`
- `http://127.0.0.1:8001/student-assignment-tracker`
- `http://127.0.0.1:8001/hermes-workflow.html`
- `http://127.0.0.1:8001/hermes-workflow`
- `http://127.0.0.1:8001/healthz`

## Local verification

Current smoke checks:

```bash
python _hermes_verify_manitoba_page.py
python _hermes_verify_student_assignment_tracker_page.py
python _hermes_verify_hermes_workflow_page.py
python _hermes_verify_subpath_root_path.py
```

The subpath check verifies the app under:

```text
/projects/practical-ai-journey
```

matching the current VPS mount path.

## VPS subpath deployment shape

Current live URL:

```text
http://142.93.152.29/projects/practical-ai-journey/
```

VPS checkout:

```text
/var/www/projects/practical-ai-journey
```

When reverse-proxied on the VPS under `/projects/practical-ai-journey/`, run the app with:

```bash
PRACTICAL_AI_ROOT_PATH=/projects/practical-ai-journey \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Use the nginx mounted-app pattern (rewrite + `X-Script-Name`) shown in:

- `deploy/nginx-practical-ai-journey.conf`

Systemd service template for the VPS user service lives at:

- `deploy/practical-ai-journey.service`

## Legacy static cleanup

The old root-level static fallback files have been removed. The FastAPI app is
the only supported website shape now:

- page templates live under `app/templates/pages/`
- shared layout lives under `app/templates/base.html` and `app/templates/partials/`
- live assets live under `static/`

## Source evidence

Draft copy is based on:

- `/Users/david/Obsidian Vault/Agent-Hermes/projects/ai-career-prep/project-evidence-review.md`
- `/Users/david/Obsidian Vault/Agent-Hermes/projects/ai-career-prep/practical-ai-journey-draft.md`

This is review copy, not final public copy.
