"""
Engola application entrypoint.

Router-split successor to the v0.5 canonical single-file app.py. Every
route that existed in app.py is preserved with identical behavior (see
core/ and routers/ for the migrated logic); new modules (career, uganda,
voice, google_oauth) are additive.

Run locally:
    uvicorn main:app --reload --port 8000

Run in Docker/Railway: see Dockerfile / railway.json (CMD now points at
main:app instead of app:app).
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.config import APP_VERSION, STATIC_DIR
from core.db import db
from routers import auth, career, chat, google_oauth, health, media, memory, permissions, uganda, voice, work

app = FastAPI(title="Engola", version=APP_VERSION)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(permissions.router)
app.include_router(media.router)
app.include_router(career.router)
app.include_router(uganda.router)
app.include_router(voice.router)
app.include_router(work.router)
app.include_router(google_oauth.router)
app.include_router(health.router)


@app.on_event("startup")
def startup():
    db().close()


@app.get("/", response_class=HTMLResponse)
def home():
    return (STATIC_DIR / "index.html").read_text()
