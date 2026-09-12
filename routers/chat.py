from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from core import ai
from core.agent import run_local
from core.config import SYSTEM_PROMPT
from core.db import db, memory_text, recent, save_message
from core.security import require_owner


router = APIRouter(prefix="/api", tags=["chat"])


def _provider_answer(text: str) -> str:
    prompt = (
        SYSTEM_PROMPT
        + "\n\nKnown owner memory:\n"
        + (memory_text() or "(none)")
    )

    msgs = [{"role": "system", "content": prompt}]
    msgs += [
        {"role": role, "content": content}
        for role, content in recent()
    ]
    msgs.append({
        "role": "user",
        "content": text,
    })

    return ai.respond(msgs)


@router.post("/chat")
async def chat(request: Request):
    denied = require_owner(request)

    if denied:
        return denied

    body = await request.json()
    text = (body.get("message") or "").strip()

    if not text:
        return JSONResponse(
            {"error": "Empty message"},
            status_code=400,
        )

    save_message("user", text)

    # Local agent runs first. This keeps Engola useful
    # without requiring a paid OpenAI API.
    local = run_local(text)

    if local.intent != "unhandled":
        save_message("assistant", local.answer)

        return {
            "answer": local.answer,
            "mode": "local",
            "intent": local.intent,
            "action": local.action,
            "executed": local.executed,
            "verified": local.verified,
            "needs_approval": local.needs_approval,
            "data": local.data,
        }


    # Optional external reasoning provider.
    if ai.is_configured():
        try:
            answer = _provider_answer(text)
        except Exception as e:
            return JSONResponse(
                {
                    "error": (
                        f"AI request failed: "
                        f"{type(e).__name__}: {e}"
                    )
                },
                status_code=502,
            )

        save_message("assistant", answer)

        return {
            "answer": answer,
            "mode": "provider",
            "intent": "reasoning",
            "executed": False,
            "verified": True,
            "needs_approval": False,
        }


    # No provider is configured. Return the local engine's
    # honest response instead of pretending the request worked.
    save_message("assistant", local.answer)

    return {
        "answer": local.answer,
        "mode": "local",
        "intent": local.intent,
        "executed": False,
        "verified": False,
        "needs_approval": False,
    }

@router.post("/clear")
def clear_chat(_: object = Depends(require_owner)):
    with db() as conn:
        conn.execute("DELETE FROM messages")
        conn.commit()
    return {"ok": True}


@router.get("/history")
def history(_: object = Depends(require_owner)):
    with db() as conn:
        rows = conn.execute(
            "SELECT role, content, ts FROM messages ORDER BY id ASC"
        ).fetchall()

        memories = conn.execute(
            "SELECT id, key, value, ts FROM memories ORDER BY id DESC"
        ).fetchall()

        permissions = conn.execute(
            "SELECT name, status, scope, updated_at "
            "FROM permissions ORDER BY name ASC"
        ).fetchall()

    return {
        "ok": True,
        "messages": [
            {"role": row[0], "content": row[1], "ts": row[2]}
            for row in rows
        ],
        "memories": [
            {"id": row[0], "key": row[1], "value": row[2], "ts": row[3]}
            for row in memories
        ],
        "permissions": [
            {
                "name": row[0],
                "status": row[1],
                "scope": row[2],
                "updated_at": row[3],
            }
            for row in permissions
        ],
    }
