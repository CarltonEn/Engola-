from pathlib import Path
import shutil

root = Path.cwd()
required = [root/'main.py', root/'core'/'db.py', root/'static']
if not all(p.exists() for p in required):
    raise SystemExit('Run this from the Engola-master repository root.')

for rel in ['core/db.py','main.py']:
    src = root/rel
    backup = root/('.v11-backup')/rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, backup)

# Add device tables without disturbing existing schema.
db = root/'core/db.py'
s = db.read_text()
needle = '    defaults = [\n'
insert = '''    c.execute(\n        """CREATE TABLE IF NOT EXISTS device_pairings(\n        id INTEGER PRIMARY KEY, code_hash TEXT UNIQUE NOT NULL,\n        created_at REAL NOT NULL, expires_at REAL NOT NULL, used_at REAL)"""\n    )\n    c.execute(\n        """CREATE TABLE IF NOT EXISTS devices(\n        device_id TEXT PRIMARY KEY, name TEXT NOT NULL, platform TEXT NOT NULL,\n        model TEXT, android_version TEXT, battery_pct REAL, charging INTEGER DEFAULT 0,\n        network_type TEXT, network_name TEXT, storage_free INTEGER, storage_total INTEGER,\n        capabilities TEXT, token_hash TEXT UNIQUE NOT NULL, created_at REAL NOT NULL,\n        last_seen REAL, status TEXT NOT NULL DEFAULT 'offline')"""\n    )\n\n'''
if 'CREATE TABLE IF NOT EXISTS devices' not in s:
    s = s.replace(needle, insert + needle, 1)
db.write_text(s)

# Copy modules.
for rel in ['core/device.py','routers/device.py']:
    dst = root/rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(root/'engola-v12-patch'/rel, dst)

main = root/'main.py'
s = main.read_text()
if 'device,' not in s:
    s = s.replace('from routers import auth, career, chat, google_oauth, health, knowledge, media, memory, permissions, uganda, voice, work',
                  'from routers import auth, career, chat, device, google_oauth, health, knowledge, media, memory, permissions, uganda, voice, work')
if 'app.include_router(device.router)' not in s:
    s = s.replace('app.include_router(auth.router)\n', 'app.include_router(auth.router)\napp.include_router(device.router)\n', 1)
needle = '<script defer src="/static/engola-v11.js"></script>'
if needle in s and 'engola-v12.js' not in s:
    s = s.replace(needle, needle + '<link rel="stylesheet" href="/static/engola-v12.css"><script defer src="/static/engola-v12.js"></script>')
main.write_text(s)

# Companion and assets are copied from the patch staging directory.
for rel in ['static/engola-v12.js','static/engola-v12.css']:
    shutil.copy2(root/'engola-v12-patch'/rel, root/rel)
(root/'tools').mkdir(exist_ok=True)
shutil.copy2(root/'engola-v12-patch/companion/engola_companion.py', root/'tools/engola_companion.py')
print('Engola v0.12 device companion patch applied.')
