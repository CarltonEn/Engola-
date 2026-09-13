from fastapi import APIRouter, Request, HTTPException
from core.capabilities import list_capabilities, get_capability
from core.security import require_owner

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])

@router.get("")
def capabilities(request: Request):
    denied = require_owner(request)
    if denied:
        return denied
    return {"ok": True, "capabilities": list_capabilities()}

@router.get("/{key}")
def capability(key: str, request: Request):
    denied = require_owner(request)
    if denied:
        return denied
    item = get_capability(key)
    if not item:
        raise HTTPException(status_code=404, detail="Unknown capability")
    return {"ok": True, "capability": item.__dict__}
