# Engola v0.6 — Private AI Chief of Staff

Engola is an owner-authenticated personal AI operating system for **Engola Innocent**.

## Architecture

This build is organized as:

```
main.py            # application entrypoint (uvicorn main:app)
app.py              # preserved v0.5 single-file baseline (uvicorn app:app), kept
                    # unmodified for reference/backward compatibility
core/
  config.py         # environment-driven settings, no hardcoded secrets
  db.py             # SQLite schema + helpers
  security.py       # sessions + WebAuthn support helpers
  ai.py             # OpenAI Responses API wrapper (honest failure if no key)
routers/
  auth.py           # WebAuthn/passkey owner authentication
  chat.py           # /api/chat, /api/history, /api/clear
  memory.py         # /api/memory
  permissions.py    # /api/permissions
  media.py          # YouTube parsing + structured Study & Learn extraction
  career.py         # transparent match scoring + hard approval gate
  uganda.py         # Uganda authoritative knowledge-source registry
  voice.py          # narration pacing/pause shaping (script only, no TTS)
  google_oauth.py   # real Google OAuth2 code flow, honest when unconfigured
  health.py         # /health
static/
  index.html        # graphite/glass frontend (existing UI, extended with
                     # Career, Uganda Knowledge, Google and Voice panels)
tests/
  test_offline.py       # see "Verifying this build" below
  _offline_stubs/        # minimal offline stand-ins for fastapi/openai/webauthn,
                         # used ONLY when those real packages aren't installed
```

Every route that existed in the original v0.5 `app.py` (`/api/auth/*`,
`/api/chat`, `/api/history`, `/api/clear`, `/api/memory`,
`/api/permissions`, `/api/media/youtube`, `/api/media/study`, `/health`)
is preserved with identical behavior in the router split. New modules
(career, Uganda registry, voice, Google OAuth) are additive.

## What is included
- WebAuthn/passkey owner authentication with required user verification.
- Owner-only session controls and challenge expiry checks.
- Graphite/black/glass-white executive UI, extended with panels for Career
  & Jobs, Uganda Knowledge, Google, and Voice Narration.
- Persistent SQLite conversation, memory, career-opportunity and
  Google-token storage.
- Permission registry for phone, computer, cloud, email, calendar,
  LinkedIn, GitHub, financial and career-submission actions.
- OpenAI Responses API integration with web search.
- Structured Study & Learn extraction (facts / claims / inferences /
  uncertainties / sources), honest about parse failures instead of
  inventing structure.
- Career Intelligence: deterministic, explainable match scoring against
  skills stored in owner memory, with a hard owner-approval gate before
  anything is marked ready. Engola has no job-board/ATS integration, so it
  never claims to have actually submitted an application anywhere.
- Uganda authoritative knowledge-source registry (URA, URSB, BoU, MoFPED,
  Judiciary, Parliament, ULRC, UIA, NSSF, UNBS) with keyword-based
  relevance detection for chat/study prompts.
- Voice narration pacing/pause shaping (sentence/paragraph segmentation,
  SSML `<break>` tags, estimated read time) — a script, not synthesized
  audio, unless a real TTS provider is wired in later.
- Google OAuth 2.0 authorization-code flow implemented with the standard
  library only (no new dependency). Fails honestly with a clear error
  when `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GOOGLE_REDIRECT_URI`
  are not set — it never pretends to be connected.
- PWA manifest/service worker for installable browser experience.
- Docker deployment support.

## Owner identity and Google integrations
See `OWNER-IDENTITY.md` and `GOOGLE-INTEGRATION.md` for the
privacy-preserving visual identity and OAuth architecture.

## Important production note
This repository is a secure prototype foundation, not a claim of
unrestricted device control. Android, desktop and cloud access must use
explicit OS/OAuth permissions. For production, migrate SQLite to a
durable Postgres/Supabase database and object storage, then add a signed
desktop agent and Android companion. Keep financial actions and career
submissions locked by default and require approval for irreversible
external actions.

## Environment
Copy `.env.example` to `.env` and configure at minimum:
- `OPENAI_API_KEY`
- `ENGOLA_SETUP_TOKEN`
- `WEBAUTHN_RP_ID`
- `WEBAUTHN_ORIGIN`
- `COOKIE_SECURE=1`

Optional, feature-gated (each fails honestly/disables itself if left blank):
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GOOGLE_SCOPES`
- `TTS_PROVIDER_API_KEY` (narration script is always available; audio synthesis is not implemented yet)

Never commit real secrets. `.gitignore` already excludes `.env` (and any
`.env.*` variant except `.env.example`), `.venv/`/`venv/`/`env/`,
`__pycache__/`, the entire `data/` directory, database/sqlite files, and
common credential/key file patterns.

## Local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Docker
```bash
docker build -t engola .
docker run --env-file .env -p 8000:8000 engola
```

## Owner setup
On the first launch, enter the one-time `ENGOLA_SETUP_TOKEN`, then approve
the platform passkey prompt. Subsequent access uses the registered owner
credential.

## Verifying this build

This build was developed in a sandbox with **no network access**, so the
real `fastapi`, `openai`, and `webauthn` packages could not be
pip-installed there to run a genuine server smoke test. Two independent
levels of verification were used, and it matters which one applies to any
given claim:

1. **Syntax check (always valid):** `python -m py_compile` on every `.py`
   file, and `node --check` on the extracted frontend JavaScript. This
   confirms there are no syntax errors anywhere, nothing more.
2. **Offline stub tests (`tests/test_offline.py`):** when the real
   `fastapi`/`openai`/`webauthn` are not installed, this suite falls back
   to a minimal local stub package (`tests/_offline_stubs/`) so the real
   application modules can still be imported and their business logic
   exercised: YouTube URL parsing, structured Study & Learn JSON parsing,
   career match scoring, the approval gate, the Uganda relevance
   heuristic, voice pacing math, and session/security helpers. **This does
   NOT validate real WebAuthn cryptographic verification, real OpenAI API
   calls, real HTTP routing, or FastAPI's dependency-injection behavior.**
   If the real packages ARE installed, the suite automatically uses them
   instead and prints which mode it ran in.

Run it with:
```bash
pip install -r requirements.txt   # once you have network access
python tests/test_offline.py -v
```

**Still required before declaring this production-ready:** run a real
`uvicorn main:app` locally (or in CI) with the actual dependencies
installed, register a passkey, exercise the WebAuthn flow with a real
browser/authenticator, and hit each endpoint with a live OpenAI key. None
of that has happened yet in this handoff.
