#!/usr/bin/env python3
"""Engola Termux knowledge acquisition + Telegram archive helper.

Free-first, stdlib-first. It can download public URLs, extract PDF text when
pypdf is installed, archive originals to Telegram, and import extracted text
into Engola using a dedicated ingestion token.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, urllib.parse
from pathlib import Path
from urllib.request import Request, urlopen
from archive import sha256_file, telegram_send_document, telegram_send_text

UA = 'Engola-Knowledge-Collector/0.13'
MAX = 49 * 1024 * 1024


def fetch(url: str) -> tuple[bytes, str, str]:
    req = Request(url, headers={'User-Agent': UA, 'Accept': 'application/pdf,text/html,text/plain,*/*;q=0.5'})
    with urlopen(req, timeout=45) as r:
        chunks=[]; total=0
        while True:
            c=r.read(256*1024)
            if not c: break
            total += len(c)
            if total > MAX: raise RuntimeError('Download exceeds 49 MB safety limit.')
            chunks.append(c)
        return b''.join(chunks), (r.headers.get('Content-Type') or '').lower(), r.geturl()


def extract(data: bytes, ctype: str, url: str) -> tuple[str, str]:
    if 'pdf' in ctype or url.lower().split('?',1)[0].endswith('.pdf'):
        try:
            from pypdf import PdfReader
        except ImportError:
            return '', 'pdf'
        from io import BytesIO
        reader=PdfReader(BytesIO(data))
        return '\n\n'.join(p.extract_text() or '' for p in reader.pages).strip(), 'pdf'
    if 'html' in ctype or '<html' in data[:500].lower().decode('utf-8','ignore'):
        text=data.decode('utf-8','replace')
        text=re.sub(r'<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', text, flags=re.I|re.S)
        text=re.sub(r'<[^>]+>', ' ', text)
        text=re.sub(r'\s+', ' ', text).strip()
        return text, 'web'
    return data.decode('utf-8','replace'), 'text'


def api_import(base: str, token: str, meta: dict, text: str) -> dict:
    payload=json.dumps({**meta, 'text': text[:2_000_000]}, ensure_ascii=False).encode()
    req=Request(base.rstrip('/')+'/api/knowledge/import', data=payload, headers={'Content-Type':'application/json','X-Engola-Ingest-Token':token,'User-Agent':UA})
    with urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode('utf-8','replace'))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('url')
    ap.add_argument('--title', default='')
    ap.add_argument('--category', default='general')
    ap.add_argument('--authority', default='reference')
    ap.add_argument('--archive', action='store_true')
    ap.add_argument('--no-import', action='store_true')
    args=ap.parse_args()
    base=os.getenv('ENGOLA_URL','').strip(); token=os.getenv('ENGOLA_INGEST_TOKEN','').strip()
    if not args.no_import and (not base or not token):
        raise SystemExit('Set ENGOLA_URL and ENGOLA_INGEST_TOKEN, or use --no-import.')
    data, ctype, final_url=fetch(args.url)
    name=Path(urllib.parse.urlparse(final_url).path).name or 'engola-source'
    out=Path(os.getenv('ENGOLA_DOWNLOAD_DIR', str(Path.home()/ 'engola-knowledge')))
    out.mkdir(parents=True, exist_ok=True)
    path=out/name
    if path.suffix == '': path=path.with_suffix('.bin')
    path.write_bytes(data)
    digest=sha256_file(path)
    text, kind=extract(data,ctype,final_url)
    meta={'url':args.url,'final_url':final_url,'title':args.title or name,'category':args.category,'authority':args.authority,'kind':kind,'sha256':digest,'characters':len(text)}
    tg=None
    if args.archive:
        tg=telegram_send_document(path, json.dumps(meta, ensure_ascii=False)[:900])
        meta['archive_provider']='telegram'; meta['archive_message_id']=tg.get('message_id'); meta['archive_file_id']=((tg.get('document') or {}).get('file_id'))
    if not args.no_import:
        if not text: raise SystemExit('No text extracted. Install pypdf for PDFs or use --no-import.')
        result=api_import(base,token,meta,text)
    else: result={'ok':True}
    print(json.dumps({'ok':True,'file':str(path),'metadata':meta,'import':result},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
