"""Encrypted API key store — DB-first, env-fallback, 60s cache."""
import time
from base64 import urlsafe_b64encode
from hashlib import sha256
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings
from app.database import engine
from sqlalchemy import text

_CACHE = {}
_CACHE_TS = 0.0
_TTL = 60

def _fernet():
    raw = (getattr(settings, "SECRET_KEY", "") or "dev-secret-change-me").encode()
    key = urlsafe_b64encode(sha256(raw).digest())
    return Fernet(key)

def _encrypt(val: str) -> str:
    return _fernet().encrypt(val.encode()).decode()

def _decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, Exception):
        return ""

def _bust(name: str):
    global _CACHE
    _CACHE.pop(name, None)

def get_key(name: str) -> str:
    """DB first, then env. Cached 60s. Returns '' if missing."""
    global _CACHE, _CACHE_TS
    now = time.time()
    if now - _CACHE_TS > _TTL:
        _CACHE = {}
        _CACHE_TS = now
    if name in _CACHE:
        return _CACHE[name]
    val = ""
    try:
        with engine.connect() as c:
            row = c.execute(
                text("SELECT value_encrypted FROM system_config WHERE key = :k"),
                {"k": name},
            ).first()
            if row and row[0]:
                val = _decrypt(row[0])
    except Exception:
        val = ""
    if not val:
        val = getattr(settings, name, "") or ""
    _CACHE[name] = val
    return val

def set_key(name: str, value: str, user_id: int = None):
    """Store encrypted. Empty value deletes the row."""
    if not value or not value.strip():
        delete_key(name)
        return
    with engine.begin() as c:
        c.execute(text("""
            INSERT INTO system_config (key, value_encrypted, updated_at, updated_by)
            VALUES (:k, :v, NOW(), :u)
            ON CONFLICT (key) DO UPDATE
              SET value_encrypted = EXCLUDED.value_encrypted,
                  updated_at = NOW(),
                  updated_by = EXCLUDED.updated_by
        """), {"k": name, "v": _encrypt(value.strip()), "u": user_id})
    _bust(name)

def delete_key(name: str):
    with engine.begin() as c:
        c.execute(text("DELETE FROM system_config WHERE key = :k"), {"k": name})
    _bust(name)

def list_keys() -> list:
    """Return metadata only — never return plaintext."""
    try:
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT key, updated_at, updated_by FROM system_config ORDER BY key"
            )).all()
            return [{"name": r[0], "updated_at": r[1].isoformat() if r[1] else None,
                     "updated_by": r[2]} for r in rows]
    except Exception:
        return []

# Known key names (used by admin panel to display all slots)
KNOWN_KEYS = [
    "GEMINI_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY",
    "GROQ_API_KEY", "GITHUB_TOKEN",
    "OPENALEX_API_KEY", "CROSSREF_MAILTO", "STACKEXCHANGE_API_KEY",
    "DEVTO_API_KEY", "USPTO_ODP_API_KEY",
    "EPO_OPS_CONSUMER_KEY", "EPO_OPS_CONSUMER_SECRET",
    "PATENTSVIEW_API_KEY", "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
]

def list_all_slots() -> list:
    """Every known key + its status (set / unset)."""
    stored = {r["name"]: r for r in list_keys()}
    out = []
    for name in KNOWN_KEYS:
        has_db = name in stored
        env_val = getattr(settings, name, "") or ""
        val = get_key(name)
        out.append({
            "name": name,
            "configured": bool(val),
            "source": "db" if has_db and stored[name].get("updated_at") else ("env" if env_val else "none"),
            "preview": f"...{val[-4:]}" if val and len(val) > 4 else ("set" if val else ""),
            "updated_at": stored[name]["updated_at"] if has_db else None,
            "updated_by": stored[name]["updated_by"] if has_db else None,
        })
    return out
