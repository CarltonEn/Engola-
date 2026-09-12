from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from core.knowledge import delete_source, get_source, ingest_url, list_sources, search_sources
from core.security import require_owner
import json
from urllib.parse import quote
from urllib.request import Request, urlopen

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

class IngestBody(BaseModel):
    url: str = Field(min_length=8, max_length=2048)

class SearchBody(BaseModel):
    query: str = Field(min_length=2, max_length=300)

@router.get("")
def knowledge_list(request: Request):
    denied = require_owner(request)
    if denied: return denied
    return {"ok": True, "sources": list_sources()}

@router.get("/{source_id}")
def knowledge_get(source_id: int, request: Request):
    denied = require_owner(request)
    if denied: return denied
    source = get_source(source_id)
    if not source:
        raise HTTPException(404, "Knowledge source not found")
    return {"ok": True, "source": source}

@router.post("/ingest")
def knowledge_ingest(body: IngestBody, request: Request):
    denied = require_owner(request)
    if denied: return denied
    try:
        return {"ok": True, "source": ingest_url(body.url)}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Engola could not ingest that source: {exc}") from exc

@router.get("/wiki")
def wiki_search(request: Request, query: str = ""):
    denied = require_owner(request)
    if denied: return denied
    q = (query or "").strip()[:120]
    if not q:
        return {"ok": True, "results": []}
    url = "https://en.wikipedia.org/w/api.php?action=opensearch&search=" + quote(q) + "&limit=6&namespace=0&format=json"
    req = Request(url, headers={"User-Agent": "Engola/0.11 (Wikipedia research)"})
    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        raise HTTPException(502, f"Wikipedia search failed: {exc}") from exc
    titles = data[1] if len(data) > 1 else []
    descriptions = data[2] if len(data) > 2 else []
    urls = data[3] if len(data) > 3 else []
    return {"ok": True, "results": [{"title": t, "description": descriptions[i] if i < len(descriptions) else "", "url": urls[i] if i < len(urls) else ""} for i, t in enumerate(titles)]}

@router.post("/search")
def knowledge_search(body: SearchBody, request: Request):
    denied = require_owner(request)
    if denied: return denied
    return {"ok": True, "results": search_sources(body.query)}

@router.delete("/{source_id}")
def knowledge_delete(source_id: int, request: Request):
    denied = require_owner(request)
    if denied: return denied
    if not delete_source(source_id):
        raise HTTPException(404, "Knowledge source not found")
    return {"ok": True, "deleted": source_id}
