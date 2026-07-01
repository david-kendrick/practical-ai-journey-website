# Practical AI Journey Draft

Local review draft for David Kendrick's first public-facing AI portfolio page.

## Run locally

One-off local server:

```bash
python3 -m http.server 4173
```

Open:

```text
http://127.0.0.1:4173/
```

## Keep it up permanently on macOS

A per-user launchd service now keeps the site running and restarts it automatically if it exits.

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
