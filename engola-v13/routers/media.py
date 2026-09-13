from __future__ import annotations
import json
import urllib.parse
import urllib.request
from urllib.parse import parse_qs, urlparse
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.security import require_owner
from core.knowledge import ingest_url

router = APIRouter(prefix='/api/media', tags=['media'])


def youtube_video_id(url: str) -> str | None:
    try:
        u = urlparse((url or '').strip())
        host = (u.hostname or '').lower()
        if host in {'youtu.be', 'www.youtu.be'}:
            return u.path.strip('/').split('/')[0] or None
        if host in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'}:
            if u.path == '/watch':
                return parse_qs(u.query).get('v', [None])[0]
            parts = u.path.strip('/').split('/')
            if len(parts) >= 2 and parts[0] in {'shorts', 'embed', 'live'}:
                return parts[1]
    except Exception:
        pass
    return None


def youtube_oembed(video_id: str) -> dict:
    try:
        target = 'https://www.youtube.com/watch?v=' + video_id
        url = 'https://www.youtube.com/oembed?url=' + urllib.parse.quote(target, safe='') + '&format=json'
        req = urllib.request.Request(url, headers={'User-Agent': 'Engola/0.13'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode('utf-8', errors='replace'))
    except Exception:
        return {}


@router.post('/youtube')
def youtube_media(body: dict, request: Request):
    denied = require_owner(request)
    if denied: return denied
    url = (body.get('url') or '').strip()
    vid = youtube_video_id(url)
    if not vid:
        return JSONResponse({'error': 'I could not identify a YouTube video from that URL.'}, 400)
    meta = youtube_oembed(vid)
    return {
        'ok': True,
        'video_id': vid,
        'embed_url': f'https://www.youtube-nocookie.com/embed/{vid}?enablejsapi=1',
        'watch_url': f'https://www.youtube.com/watch?v={vid}',
        'title': meta.get('title', 'YouTube video'),
        'author': meta.get('author_name', ''),
        'thumbnail': meta.get('thumbnail_url', ''),
        'source_mode': 'metadata',
        'truth_note': 'Engola has metadata/player access here; this is not evidence that Engola watched or heard the video.'
    }


@router.post('/study')
def study_media(body: dict, request: Request):
    denied = require_owner(request)
    if denied: return denied
    url = (body.get('url') or '').strip()
    title = (body.get('title') or '').strip()
    if not url:
        return JSONResponse({'error': 'Media URL required.'}, 400)
    try:
        source = ingest_url(url)
    except Exception as exc:
        return JSONResponse({'error': f'Media study could not obtain readable transcript/content: {exc}', 'source_mode': 'unavailable'}, 502)
    return {
        'ok': True,
        'source': source,
        'title': title or source.get('title'),
        'answer': 'Transcript/content has been imported into the Engola Knowledge Vault. Ask Engola to summarize, teach, quiz, or connect this material to another source.',
        'source_mode': 'transcript',
        'truth_note': 'This study result is transcript/content-derived; it does not claim audiovisual viewing.'
    }
