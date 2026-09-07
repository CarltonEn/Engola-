from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.db import remember
from core.security import require_owner

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.post("")
async def add_memory(request: Request):
    denied = require_owner(request)
    if denied:
        return denied
    b = await request.json()
    key = (b.get("key") or "").strip()
    value = (b.get("value") or "").strip()
    if not key or not value:
        return JSONResponse({"error": "key and value required"}, status_code=400)
    remember(key, value)
    return {"ok": True}
