"""Password hashing and opaque session token handling."""

from __future__ import annotations

import hashlib
import secrets
import bcrypt


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))


def new_opaque_token() -> tuple[str, str]:
    """Return ``(raw_token, token_hash)`` for storage in ``auth.sessions.token_hash``."""
    raw = secrets.token_urlsafe(48)
    digest = hashlib.sha256(raw.encode("ascii")).hexdigest()
    return raw, digest


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("ascii")).hexdigest()
