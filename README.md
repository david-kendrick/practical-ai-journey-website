# Practical AI Journey Draft

Local review draft for David Kendrick's first public-facing AI portfolio page.

## Run locally

One-off static server:

```bash
python3 -m http.server 4173
```

Open:

```text
http://127.0.0.1:4173/
```

## Run the FastAPI app locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

FastAPI pages available locally:

- `http://127.0.0.1:8001/`
- `http://127.0.0.1:8001/index.html`
- `http://127.0.0.1:8001/manitoba-cottage-search.html`
- `http://127.0.0.1:8001/student-assignment-tracker.html`
- `http://127.0.0.1:8001/hermes-workflow.html`
- `http://127.0.0.1:8001/healthz`

## VPS subpath deployment shape

When reverse-proxied on the VPS under `/projects/practical-ai-journey/`, run the
app with:

```bash
PRACTICAL_AI_ROOT_PATH=/projects/practical-ai-journey \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Use the nginx mounted-app pattern (rewrite + `X-Script-Name`) shown in:

- `deploy/nginx-practical-ai-journey.conf`

Systemd service template for the VPS user service lives at:

- `deploy/practical-ai-journey.service`

## Keep the old static preview up on macOS

A per-user launchd service now keeps the original static preview server running and restarts it automatically if it exits.

LaunchAgent plist:

```text
~/Library/LaunchAgents/com.david.practical-ai-journey-site.plist
```

Useful commands:

```bash
# Reload the service
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.david.practical-ai-journey-site.plist || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.david.practical-ai-journey-site.plist
launchctl kickstart -k gui/$(id -u)/com.david.practical-ai-journey-site

# Inspect status
launchctl print gui/$(id -u)/com.david.practical-ai-journey-site

# Stop it
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.david.practical-ai-journey-site.plist
```

Logs:

```text
~/Library/Logs/practical-ai-journey-site.log
~/Library/Logs/practical-ai-journey-site.err.log
```

## Source evidence

Draft copy is based on:

- `/Users/david/Obsidian Vault/Agent-Hermes/projects/ai-career-prep/project-evidence-review.md`
- `/Users/david/Obsidian Vault/Agent-Hermes/projects/ai-career-prep/practical-ai-journey-draft.md`

This is review copy, not final public copy.
