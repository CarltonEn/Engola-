from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core import ai
from core.config import SYSTEM_PROMPT
from core.db import memory_text, recent, save_message
from core.security import require_owner

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(request: Request):
    denied = require_owner(request)
    if denied:
        return denied
    body = await request.json()
    text = (body.get("message") or "").strip()
    if not text:
        return JSONResponse({"error": "Empty message"}, status_code=400)
    if not ai.is_configured():
        return JSONResponse({"error": "OPENAI_API_KEY is not configured on the server."}, status_code=503)
    save_message("user", text)
    prompt = SYSTEM_PROMPT + "\n\nKnown owner memory:\n" + (memory_text() or "(none)")
    msgs = [{"role": "system", "content": prompt}] + [{"role": r, "content": c} for r, c in recent()]
    try:
        answer = ai.respond(msgs)
    except Exception as e:
        return JSONResponse({"error": f"AI request failed: {type(e).__name__}: {e}"}, status_code=502)
    save_message("assistant", answer)
    return {"answer": answer}


@router.post("/clear")
def clear(request: Request):
    denied = require_owner(request)
    if denied:
        return denied
    from core.db import db

    c = db()
    c.execute("DELETE FROM messages")
    c.commit()
    c.close()
    return {"ok": True}


@router.get("/history")
def history(request: Request):
    denied = require_owner(request)
    if denied:
        return denied
    from core.db import db

    c = db()
    perms = [
        {"name": r[0], "status": r[1], "scope": r[2]}
        for r in c.execute("SELECT name,status,scope FROM permissions ORDER BY name")
    ]
    c.close()
    return {
        "messages": [{"role": r, "content": c} for r, c in recent()],
        "memories": memory_text(),
        "permissions": perms,
    }
