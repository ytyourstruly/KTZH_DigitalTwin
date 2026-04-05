"""HttpOnly session cookie helpers (same opaque token as Bearer)."""

from __future__ import annotations

from datetime import UTC, datetime

from starlette.responses import Response

from app.core.config import get_settings


def _ttl_seconds(expires_at: datetime) -> int:
    now = datetime.now(UTC)
    exp = expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    return max(0, int((exp - now).total_seconds()))


def attach_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    s = get_settings()
    response.set_cookie(
        key=s.session_cookie_name,
        value=token,
        max_age=_ttl_seconds(expires_at),
        path=s.session_cookie_path,
        domain=s.session_cookie_domain,
        secure=s.session_cookie_secure,
        httponly=True,
        samesite=s.session_cookie_samesite,
    )


def clear_session_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(
        key=s.session_cookie_name,
        path=s.session_cookie_path,
        domain=s.session_cookie_domain,
    )
