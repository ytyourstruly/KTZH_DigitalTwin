"""Shared SQLAlchemy repository wiring.

Concrete repos live in ``auth/`` and ``loco/`` (one module per persistence port).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyRepository:
    """Holds the async session used for all operations in this unit of work."""

    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
