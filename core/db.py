"""
SQLite persistence layer.

This preserves the exact schema and helper behavior from the v0.5 canonical
single-file app.py, plus additive tables for the career module and Uganda
knowledge registry. No existing table, column or behavior was removed or
changed.
"""
import sqlite3
import time

from core.config import DB_PATH


def db() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.execute(
        "CREATE TABLE IF NOT EXISTS messages("
        "id INTEGER PRIMARY KEY, role TEXT, content TEXT, ts REAL)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS memories("
        "id INTEGER PRIMARY KEY, key TEXT UNIQUE, value TEXT, ts REAL)"
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS owner_credentials(
        id INTEGER PRIMARY KEY, credential_id TEXT UNIQUE NOT NULL,
        public_key BLOB NOT NULL, sign_count INTEGER NOT NULL DEFAULT 0,
        created_at REAL NOT NULL)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS webauthn_challenges(
        id INTEGER PRIMARY KEY, kind TEXT NOT NULL, challenge BLOB NOT NULL,
        created_at REAL NOT NULL)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS sessions(
        token_hash TEXT PRIMARY KEY, created_at REAL NOT NULL,
        last_seen REAL NOT NULL, expires_at REAL NOT NULL)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS permissions(
        name TEXT PRIMARY KEY, status TEXT NOT NULL, scope TEXT NOT NULL,
        updated_at REAL NOT NULL)"""
    )
    # Additive: career module
    c.execute(
        """CREATE TABLE IF NOT EXISTS career_opportunities(
        id INTEGER PRIMARY KEY, title TEXT NOT NULL, company TEXT,
        url TEXT, description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft',
        score REAL, score_breakdown TEXT, created_at REAL NOT NULL,
        updated_at REAL NOT NULL)"""
    )
    # Additive: Google OAuth token storage (owner-only, single row)
    c.execute(
        """CREATE TABLE IF NOT EXISTS google_tokens(
        id INTEGER PRIMARY KEY CHECK (id = 1), access_token TEXT,
        refresh_token TEXT, scope TEXT, expires_at REAL, updated_at REAL)"""
    )

    defaults = [
        ("phone", "ask", "contacts, files, camera, microphone, notifications"),
        ("computer", "ask", "files, apps, browser, local automation"),
        ("cloud", "ask", "Drive/OneDrive/Dropbox and connected storage"),
        ("email", "ask", "read/search; send requires approval"),
        ("calendar", "ask", "read/write after permission"),
        ("linkedin", "ask", "profile and approved job-search data"),
        ("github", "ask", "repositories and development workflows"),
        ("financial", "deny", "banking/payment actions remain locked by default"),
        ("career_submission", "deny", "submitting applications on the owner's behalf"),
    ]
    for row in defaults:
        c.execute(
            "INSERT OR IGNORE INTO permissions(name,status,scope,updated_at) VALUES(?,?,?,?)",
            (*row, time.time()),
        )
    c.commit()
    return c


def recent(limit: int = 30):
    c = db()
    rows = c.execute(
        "SELECT role,content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    return list(reversed(rows))


def memory_text(limit: int = 150) -> str:
    c = db()
    rows = c.execute(
        "SELECT key,value FROM memories ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    return "\n".join(f"- {k}: {v}" for k, v in rows)


def save_message(role: str, content: str):
    c = db()
    c.execute(
        "INSERT INTO messages(role,content,ts) VALUES(?,?,?)",
        (role, content, time.time()),
    )
    c.commit()
    c.close()


def remember(key: str, value: str):
    c = db()
    c.execute(
        "INSERT INTO memories(key,value,ts) VALUES(?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value,ts=excluded.ts",
        (key, value, time.time()),
    )
    c.commit()
    c.close()


def has_owner() -> bool:
    c = db()
    n = c.execute("SELECT COUNT(*) FROM owner_credentials").fetchone()[0]
    c.close()
    return n > 0


def credential_count() -> int:
    c = db()
    n = c.execute("SELECT COUNT(*) FROM owner_credentials").fetchone()[0]
    c.close()
    return n
