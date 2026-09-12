from pathlib import Path
import shutil

ROOT = Path.cwd()
PATCH = Path(__file__).resolve().parent
if not (ROOT / "main.py").exists() or not (ROOT / "core" / "db.py").exists():
    raise SystemExit("Run this from the Engola-master repository root (where main.py exists).")


def backup(path):
    b = path.with_suffix(path.suffix + '.v10-backup')
    if path.exists() and not b.exists():
        shutil.copy2(path, b)

# The script is intended to be run from the repository root after the patch
# directory has been copied/extracted there.
for rel in ['core/db.py','main.py','requirements.txt']:
    backup(ROOT/rel)

# Copy new modules/assets.
for rel in ['core/knowledge.py','routers/knowledge.py','static/engola-v11.css','static/engola-v11.js','README-v0.11.md']:
    src = PATCH/rel
    if not src.exists():
        if rel == 'README-v0.11.md':
            src = PATCH/'README.md'
        else:
            continue
    dst = ROOT/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

# Database migration.
db = ROOT/'core/db.py'
s = db.read_text()
needle = '''    # Additive: Google OAuth token storage (owner-only, single row)\n'''
insert = '''    # Additive: v0.11 private knowledge vault\n    c.execute(\n        """CREATE TABLE IF NOT EXISTS knowledge_sources(\n        id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, title TEXT NOT NULL,\n        kind TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ready',\n        metadata TEXT NOT NULL DEFAULT '{}', text TEXT NOT NULL,\n        created_at REAL NOT NULL, updated_at REAL NOT NULL)"""\n    )\n\n'''
if 'CREATE TABLE IF NOT EXISTS knowledge_sources' not in s:
    if needle not in s:
        raise SystemExit('Could not find safe db.py insertion point')
    s = s.replace(needle, insert + needle, 1)
db.write_text(s)

# Requirements: pure-python, no Rust toolchain.
req = ROOT/'requirements.txt'
rs = req.read_text()
for line in ['pypdf==6.18.0\n','youtube-transcript-api==1.2.0\n']:
    if line.strip() not in rs:
        rs += line
req.write_text(rs)

# Entrypoint: register the router and inject the visual layer into the existing
# index at response time, avoiding a risky replacement of the proven v0.10 UI.
main = ROOT/'main.py'
ms = main.read_text()
ms = ms.replace('from routers import auth, career, chat, google_oauth, health, media, memory, permissions, uganda, voice, work\n', 'from routers import auth, career, chat, google_oauth, health, knowledge, media, memory, permissions, uganda, voice, work\n')
if 'app.include_router(knowledge.router)' not in ms:
    ms = ms.replace('app.include_router(memory.router)\n', 'app.include_router(memory.router)\napp.include_router(knowledge.router)\n', 1)
old = '''@app.get("/", response_class=HTMLResponse)\ndef home():\n    return (STATIC_DIR / "index.html").read_text()\n'''
new = '''@app.get("/", response_class=HTMLResponse)\ndef home():\n    html = (STATIC_DIR / "index.html").read_text()\n    marker = '</head>'\n    addons = '<link rel="stylesheet" href="/static/engola-v11.css"><script defer src="/static/engola-v11.js"></script>'\n    return HTMLResponse(html.replace(marker, addons + marker, 1))\n'''
if old in ms:
    ms = ms.replace(old, new, 1)
else:
    raise SystemExit('Could not find safe home() block in main.py')
main.write_text(ms)

print('Engola v0.11 patch applied.')
print('Backups created with .v10-backup suffix where applicable.')
