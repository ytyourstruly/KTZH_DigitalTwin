from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.auth import User
from app.repositories.protocols import UserRepository


class UserService:
    """Use-cases for ``auth.users``; persistence via :class:`UserRepository` only."""

    __slots__ = ("_users",)

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._users.get_by_id(user_id)

    async def require_by_id(self, user_id: UUID) -> User:
        user = await self.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", code="user_not_found")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self._users.get_by_email(email)

    async def get_by_username(self, username: str) -> User | None:
        return await self._users.get_by_username(username)

    async def register(self, user: User) -> None:
        await self._users.add(user)

    async def remove(self, user: User) -> None:
        await self._users.delete(user)
