from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.auth import AuthSession
from app.repositories.protocols import AuthSessionRepository


class AuthSessionService:
    """Use-cases for ``auth.sessions``."""

    __slots__ = ("_sessions",)

    def __init__(self, sessions: AuthSessionRepository) -> None:
        self._sessions = sessions

    async def get_by_id(self, session_id: UUID) -> AuthSession | None:
        return await self._sessions.get_by_id(session_id)

    async def require_by_id(self, session_id: UUID) -> AuthSession:
        row = await self.get_by_id(session_id)
        if row is None:
            raise NotFoundError("Session not found", code="session_not_found")
        return row

    async def get_by_token_hash(self, token_hash: str) -> AuthSession | None:
        return await self._sessions.get_by_token_hash(token_hash)

    async def create(self, session: AuthSession) -> None:
        await self._sessions.add(session)

    async def revoke(self, session: AuthSession) -> None:
        await self._sessions.delete(session)
