import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from jose import JWTError, jwt
import bcrypt

# Ensure .env is loaded even if this module is imported before app.config
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY or SECRET_KEY == "change-me-in-production-use-a-long-random-string":
    raise RuntimeError(
        "SECRET_KEY is not set. Add SECRET_KEY=\"<random>\" to backend/.env "
        "and restart the backend. Generate one with:\n"
        "    python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    """Hash a password with bcrypt. Truncates to 72 bytes (bcrypt limit)."""
    pw_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        pw_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def generate_refresh_token() -> str:
    """Opaque random token (not JWT)."""
    return secrets.token_urlsafe(48)
