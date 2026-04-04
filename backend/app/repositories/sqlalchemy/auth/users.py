from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.auth import User
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyUserRepository(SqlAlchemyRepository):
    """``auth.users`` — :class:`~app.repositories.protocols.UserRepository`."""

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def add(self, user: User) -> None:
        self._session.add(user)
        await self._session.flush()

    async def delete(self, user: User) -> None:
        await self._session.delete(user)
