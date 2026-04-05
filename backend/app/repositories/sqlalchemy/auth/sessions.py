from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.auth import AuthSession
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyAuthSessionRepository(SqlAlchemyRepository):
    """``auth.sessions`` — :class:`~app.repositories.protocols.AuthSessionRepository`."""

    async def get_by_id(self, session_id: UUID) -> AuthSession | None:
        result = await self._session.execute(
            select(AuthSession).where(AuthSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> AuthSession | None:
        result = await self._session.execute(
            select(AuthSession).where(AuthSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def add(self, session: AuthSession) -> None:
        self._session.add(session)

    async def delete(self, session: AuthSession) -> None:
        await self._session.delete(session)
