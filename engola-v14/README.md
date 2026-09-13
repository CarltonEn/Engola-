# Engola v0.14 — Research + Knowledge Usability

This patch turns the existing v0.11–v0.13 knowledge/media foundation into a usable Research workspace and connects stored knowledge to owner chat when no paid AI provider is configured.

## Changes
- Research UI rebuilt as a coherent v0.14 workspace.
- Fixes the `[object Object]` Wikipedia rendering by using explicit fields.
- Public source acquisition remains owner-authenticated.
- YouTube preview uses the existing privacy-enhanced embed endpoint.
- Free-first Media Study path acquires publicly available page/transcript text into the vault when OpenAI is not configured.
- Knowledge Vault search returns compact excerpts.
- Owner chat can return grounded vault evidence without OpenAI instead of only saying the request is unhandled.
- `/api/health` aliases `/health`.
- Application version becomes `0.14.0`.

## Apply
Run from `~/Engola-master`:

```bash
unzip -o ~/downloads/Engola-v0.14-research-knowledge.patch.zip
python engola-v14/upgrade_v14.py
python -m py_compile core/config.py core/health.py 2>/dev/null || true
python -m py_compile core/knowledge.py routers/knowledge.py routers/media.py routers/chat.py routers/health.py main.py
```

Do not commit/deploy until the syntax check passes.
