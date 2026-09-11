"""
Central configuration for Engola.

All values are read from the environment (see .env.example). Nothing here
invents a credential or a default secret. Where a value is security-sensitive
(setup token, WebAuthn RP id/origin, OAuth client credentials) an empty value
means the corresponding feature honestly reports itself as unconfigured
instead of silently working with a fake/default credential.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "engola.db"
STATIC_DIR = BASE_DIR / "static"

# Identity / product
OWNER_NAME = os.getenv("ENGOLA_OWNER_NAME", "Engola Innocent")
APP_VERSION = "0.7.0"

# Sessions
SESSION_COOKIE = "engola_session"
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", "43200"))
IDLE_TTL = int(os.getenv("SESSION_IDLE_SECONDS", "1800"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "1") == "1"

# WebAuthn
RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "Engola")
WEBAUTHN_RP_ID = os.getenv("WEBAUTHN_RP_ID", "").strip()
WEBAUTHN_ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "").strip()
ENGOLA_SETUP_TOKEN = os.getenv("ENGOLA_SETUP_TOKEN", "").strip()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
ENGOLA_MODEL = os.getenv("ENGOLA_MODEL", "gpt-5.6")

# Google OAuth (owner-provided; absent by default -> feature reports
# "not configured" rather than faking success)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
GOOGLE_SCOPES = os.getenv(
    "GOOGLE_SCOPES",
    "openid email profile https://www.googleapis.com/auth/calendar.readonly",
).strip()

SYSTEM_PROMPT = f"""You are Engola, the private AI chief of staff for {OWNER_NAME}, the sole owner.
Once authenticated, address him as "Sir". Be calm, intelligent, strategic, concise and highly action-oriented.
Primary objective: maximize {OWNER_NAME}'s legitimate success while protecting his privacy, assets, reputation, opportunities and digital security.
Continuously improve from explicit feedback and useful owner preferences, but never silently weaken authentication, permissions or safety controls.
Use current authoritative sources for time-sensitive questions and clearly separate facts, inference and uncertainty.
For Uganda tax, accounting, business and legal questions, prefer primary sources and identify the date/version of law or guidance.
Never invent completed actions, permissions, sources, credentials or biometric verification.
Before irreversible or externally consequential actions, obtain explicit confirmation unless the owner has granted a specific standing permission.
Be assertive and strategic, but lawful, truthful and security-conscious.
For spoken responses, use a warm, deep, measured British documentary-narration style. Do not imitate, clone or claim to reproduce any living narrator's distinctive voice."""
