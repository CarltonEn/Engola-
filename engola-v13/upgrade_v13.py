from __future__ import annotations
import shutil, time
from pathlib import Path

PATCH_DIR=Path(__file__).resolve().parent
ROOT=PATCH_DIR.parent
BACKUP=ROOT/'.v13-backup'

def backup(path):
    if path.exists():
        BACKUP.mkdir(exist_ok=True)
        shutil.copy2(path, BACKUP/path.name)

def patch_knowledge():
    p=ROOT/'core'/'knowledge.py'
    if not p.exists(): raise SystemExit('core/knowledge.py not found; apply v0.11/v0.12 first.')
    backup(p)
    s=p.read_text()
    if 'def import_text_source(' not in s:
        s += r'''

def import_text_source(*, url: str, title: str, kind: str, text: str, metadata: dict | None = None) -> dict:
    """Import text acquired outside Railway (e.g. Termux) without storing the original binary."""
    import json as _json, time as _time
    clean=(text or '').strip()
    if not clean: raise ValueError('No readable text supplied.')
    clean=clean[:MAX_TEXT]
    metadata=metadata or {}
    conn=db()
    existing=conn.execute('SELECT id FROM knowledge_sources WHERE url=? AND status=\'ready\' ORDER BY id DESC LIMIT 1',(url,)).fetchone()
    if existing:
        conn.execute('UPDATE knowledge_sources SET title=?,kind=?,metadata=?,text=?,updated_at=? WHERE id=?',(title[:300],kind,_json.dumps(metadata,ensure_ascii=False),clean,_time.time(),existing[0]))
        source_id=existing[0]
    else:
        now=_time.time()
        cur=conn.execute('INSERT INTO knowledge_sources(url,title,kind,status,metadata,text,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(url,title[:300],kind,'ready',_json.dumps(metadata,ensure_ascii=False),clean,now,now))
        source_id=cur.lastrowid
    conn.commit(); conn.close()
    return {'id':source_id,'url':url,'title':title[:300],'kind':kind,'characters':len(clean),'metadata':metadata}
'''
        p.write_text(s)

def patch_router():
    p=ROOT/'routers'/'knowledge.py'
    if not p.exists(): raise SystemExit('routers/knowledge.py not found; apply v0.11/v0.12 first.')
    backup(p)
    s=p.read_text()
    s=s.replace('from core.knowledge import delete_source, get_source, ingest_url, list_sources, search_sources','from core.knowledge import delete_source, get_source, ingest_url, list_sources, search_sources, import_text_source')
    if 'ENGOLA_INGEST_TOKEN' not in s:
        s=s.replace('import json\n','import json\nimport os\n')
    if '@router.post("/import")' not in s and "@router.post('/import')" not in s:
        s += r'''

@router.post('/import')
def knowledge_import(body: dict, request: Request):
    # Termux acquisition uses a separate ingestion token so WebAuthn does not
    # need to be automated on the phone. Keep this token out of browser code.
    expected=(os.getenv('ENGOLA_INGEST_TOKEN') or '').strip()
    supplied=(request.headers.get('X-Engola-Ingest-Token') or '').strip()
    if not expected or not supplied or not __import__('secrets').compare_digest(expected,supplied):
        return JSONResponse({'error':'Invalid ingestion authorization.'},403)
    text=(body.get('text') or '').strip()
    url=(body.get('url') or body.get('final_url') or '').strip()
    if not text or not url:
        return JSONResponse({'error':'url and text are required.'},400)
    source=import_text_source(url=url,title=(body.get('title') or url).strip(),kind=(body.get('kind') or 'external').strip(),text=text,metadata=body.get('metadata') or {k:body[k] for k in ('category','authority','sha256','archive_provider','archive_message_id','archive_file_id') if k in body})
    return {'ok':True,'source':source}
'''
        # JSONResponse already imported in v11? add if not.
        if 'from fastapi.responses import JSONResponse' not in s:
            s=s.replace('from fastapi import APIRouter, HTTPException, Request','from fastapi import APIRouter, HTTPException, Request\nfrom fastapi.responses import JSONResponse')
    p.write_text(s)

def patch_main():
    p=ROOT/'main.py'
    if not p.exists(): raise SystemExit('main.py not found.')
    backup(p)
    s=p.read_text()
    if 'from routers.media import router as media_router' not in s:
        # insert after router imports
        marker='from routers.'
        lines=s.splitlines()
        idx=next((i for i,l in enumerate(lines) if l.startswith('from routers.')),0)
        lines.insert(idx,'from routers.media import router as media_router')
        s='\n'.join(lines)+'\n'
    if 'include_router(media_router)' not in s:
        lines=s.splitlines()
        # after last include_router line
        inds=[i for i,l in enumerate(lines) if 'app.include_router(' in l]
        if inds: lines.insert(inds[-1]+1,'app.include_router(media_router)')
        else: raise SystemExit('Could not locate app.include_router(...) in main.py')
        s='\n'.join(lines)+'\n'
    p.write_text(s)

def main():
    patch_knowledge(); patch_router(); patch_main()
    print('Engola v0.13 patch applied. Backups: .v12-backup/')

if __name__=='__main__': main()
