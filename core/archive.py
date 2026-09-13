from __future__ import annotations
import hashlib, json, os, time
from pathlib import Path
from urllib.request import Request, urlopen

TELEGRAM_API = 'https://api.telegram.org/bot{}/{}'
MAX_TELEGRAM_BYTES = 49 * 1024 * 1024


def _cfg(name: str) -> str:
    return (os.getenv(name) or '').strip()


def telegram_configured() -> bool:
    return bool(_cfg('ENGOLA_TELEGRAM_BOT_TOKEN') and _cfg('ENGOLA_TELEGRAM_CHAT_ID'))


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def telegram_send_document(path: str | Path, caption: str = '') -> dict:
    token = _cfg('ENGOLA_TELEGRAM_BOT_TOKEN')
    chat_id = _cfg('ENGOLA_TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        raise RuntimeError('Telegram archive is not configured.')
    path = Path(path)
    size = path.stat().st_size
    if size > MAX_TELEGRAM_BYTES:
        raise ValueError('File is larger than the standard Telegram Bot API upload limit.')
    # stdlib multipart/form-data; no third-party package required.
    boundary = '----EngolaBoundary' + hashlib.sha256(os.urandom(16)).hexdigest()[:20]
    parts = []
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n').encode())
    if caption:
        safe_caption = caption[:900]
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{safe_caption}\r\n').encode())
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{path.name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode())
    with open(path, 'rb') as f:
        body = b''.join(parts) + f.read() + f'\r\n--{boundary}--\r\n'.encode()
    url = TELEGRAM_API.format(token, 'sendDocument')
    req = Request(url, data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}', 'User-Agent': 'Engola-Termux/0.13'})
    with urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode('utf-8', errors='replace'))
    if not data.get('ok'):
        raise RuntimeError(data.get('description') or 'Telegram rejected the document.')
    return data.get('result') or {}


def telegram_send_text(text: str) -> dict:
    token = _cfg('ENGOLA_TELEGRAM_BOT_TOKEN')
    chat_id = _cfg('ENGOLA_TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        raise RuntimeError('Telegram archive is not configured.')
    payload = json.dumps({'chat_id': chat_id, 'text': text[:3900]}, ensure_ascii=False).encode()
    req = Request(TELEGRAM_API.format(token, 'sendMessage'), data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Engola-Termux/0.13'})
    with urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode('utf-8', errors='replace'))
    if not data.get('ok'):
        raise RuntimeError(data.get('description') or 'Telegram rejected the message.')
    return data.get('result') or {}
