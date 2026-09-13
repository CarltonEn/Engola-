from __future__ import annotations
import os, shutil
from pathlib import Path

PATCH_ROOT=Path(__file__).resolve().parent
REPO=Path(os.getenv('ENGOLA_REPO_ROOT','')).expanduser() if os.getenv('ENGOLA_REPO_ROOT') else Path.cwd()
if not (REPO/'main.py').exists() or not (REPO/'static'/'index.html').exists():
    raise SystemExit(f'Engola repo not found at {REPO}. Run this from ~/Engola-master.')
BACKUP=REPO/'.v14-backup'
BACKUP.mkdir(exist_ok=True)

def backup(path: Path):
    if path.exists(): shutil.copy2(path, BACKUP/path.name.replace('/','_'))

def inject_once(path: Path, marker: str, payload: str, needle: str):
    s=path.read_text(encoding='utf-8')
    if marker in s: return False
    if needle not in s: raise RuntimeError(f'Could not find insertion point in {path}')
    path.write_text(s.replace(needle,payload+needle,1),encoding='utf-8')
    return True

# Static assets
for rel in ('engola-v14.css','engola-v14.js'):
    src=PATCH_ROOT/'static'/rel; dst=REPO/'static'/rel; backup(dst); shutil.copy2(src,dst)
idx=REPO/'static'/'index.html'; backup(idx)
s=idx.read_text(encoding='utf-8')
if '/static/engola-v14.css' not in s:
    s=s.replace('</head>','<link rel="stylesheet" href="/static/engola-v14.css">\n</head>',1)
if '/static/engola-v14.js' not in s:
    s=s.replace('</body>','<script src="/static/engola-v14.js"></script>\n</body>',1)
idx.write_text(s,encoding='utf-8')

# Version and health alias.
config=REPO/'core'/'config.py'; backup(config)
s=config.read_text(encoding='utf-8').replace('APP_VERSION = "0.10.0"','APP_VERSION = "0.14.0"')
config.write_text(s,encoding='utf-8')
health=REPO/'routers'/'health.py'; backup(health)
s=health.read_text(encoding='utf-8')
if '@router.get("/api/health")' not in s:
    s=s.replace('@router.get("/health")','@router.get("/health")\n@router.get("/api/health")',1)
health.write_text(s,encoding='utf-8')

# Make media Study & Learn work without OpenAI: transcript/extraction first.
media=REPO/'routers'/'media.py'; backup(media)
s=media.read_text(encoding='utf-8')
if 'from core.knowledge import ingest_url' not in s:
    s=s.replace('from core.db import remember, save_message','from core.db import remember, save_message\nfrom core.knowledge import ingest_url',1)
needle='    if not ai.is_configured():\n        return JSONResponse({"error": "OPENAI_API_KEY is not configured on the server."}, status_code=503)'
replacement='''    if not ai.is_configured():\n        # Free-first path: acquire the public page/video transcript into the vault.\n        try:\n            source = ingest_url(url)\n            text = (source.get("text") or "").strip()\n            excerpt = text[:12000]\n            return {\n                "mode": "free",\n                "stored": True,\n                "source": {k: source.get(k) for k in ("id", "url", "title", "kind", "status", "characters")},\n                "excerpt": excerpt,\n                "message": "I did not watch or listen to the media. I acquired the publicly available text/transcript and stored it for study."\n            }\n        except Exception as e:\n            return JSONResponse({"error": f"Free media acquisition failed: {type(e).__name__}: {e}"}, status_code=502)'''
if needle not in s: raise RuntimeError('Expected media AI guard not found')
s=s.replace(needle,replacement,1)
media.write_text(s,encoding='utf-8')

# Knowledge search results should contain a useful excerpt for the UI/chat.
knowledge=REPO/'core'/'knowledge.py'; backup(knowledge)
s=knowledge.read_text(encoding='utf-8')
old='''def search_sources(query: str, limit: int = 8) -> list[dict[str, Any]]:\n'''
# Don't rewrite the search implementation; append a helper used by chat if absent.
if 'def search_for_chat(' not in s:
    s += '''\n\ndef search_for_chat(query: str, limit: int = 4) -> list[dict[str, Any]]:\n    """Return compact evidence records suitable for owner chat without an LLM."""\n    rows = search_sources(query, limit=limit)\n    out=[]\n    q=(query or "").strip().lower()\n    for row in rows:\n        text=(row.get("text") or row.get("excerpt") or "").strip()\n        if not text:\n            continue\n        pos=text.lower().find(q) if q else -1\n        if pos < 0:\n            pos=0\n        start=max(0,pos-350); end=min(len(text),pos+1400)\n        out.append({"id":row.get("id"),"title":row.get("title"),"url":row.get("url"),"kind":row.get("kind"),"excerpt":text[start:end]})\n    return out\n'''
knowledge.write_text(s,encoding='utf-8')

# Connect knowledge evidence to chat when the local agent has no dedicated action and no provider is configured.
chat=REPO/'routers'/'chat.py'; backup(chat)
s=chat.read_text(encoding='utf-8')
if 'from core.knowledge import search_for_chat' not in s:
    s=s.replace('from core.security import require_owner','from core.security import require_owner\nfrom core.knowledge import search_for_chat',1)
needle='''    # Optional external reasoning provider.\n    if ai.is_configured():'''
replacement='''    # Vault-backed evidence path works without a paid AI provider.\n    try:\n        evidence = search_for_chat(text, limit=4)\n    except Exception:\n        evidence = []\n    if evidence and not ai.is_configured():\n        blocks=[]\n        for item in evidence:\n            blocks.append(f"SOURCE: {item.get('title') or item.get('url') or 'Stored source'}\\nURL: {item.get('url') or ''}\\n{item.get('excerpt') or ''}")\n        answer = (\n            "I found relevant material in your Knowledge Vault. I can ground this answer in these stored sources, "\n            "but I will not pretend to have performed deeper interpretation without a reasoning provider.\\n\\n"\n            + "\\n\\n---\\n\\n".join(blocks)\n        )\n        save_message("assistant", answer)\n        return {"answer": answer, "mode": "knowledge", "intent": "knowledge_lookup", "action": "search_knowledge_vault", "executed": True, "verified": True, "needs_approval": False, "data": {"sources": evidence}}\n\n    # Optional external reasoning provider.\n    if ai.is_configured():'''
if needle not in s: raise RuntimeError('Expected chat provider marker not found')
s=s.replace(needle,replacement,1)
# Add vault context to provider prompt.
needle='''    if ai.is_configured():\n        try:\n            answer = _provider_answer(text)'''
replacement='''    if ai.is_configured():\n        try:\n            answer = _provider_answer(text)'''
# Leave provider architecture untouched for now; no accidental prompt changes.
chat.write_text(s,encoding='utf-8')

print('Engola v0.14 patch applied.')
print(f'Repo: {REPO}')
print(f'Backups: {BACKUP}')
