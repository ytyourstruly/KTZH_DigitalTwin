from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.loco import Locomotive, LocomotiveStatus
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyLocomotiveRepository(SqlAlchemyRepository):
    """``loco.locomotives`` — :class:`~app.repositories.protocols.LocomotiveRepository`."""

    async def get_by_id(self, locomotive_id: UUID) -> Locomotive | None:
        result = await self._session.execute(
            select(Locomotive).where(Locomotive.id == locomotive_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Locomotive | None:
        result = await self._session.execute(select(Locomotive).where(Locomotive.code == code))
        return result.scalar_one_or_none()

    async def list_page(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Locomotive]:
        stmt = (
            select(Locomotive)
            .order_by(Locomotive.code)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: LocomotiveStatus,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Locomotive]:
        stmt = (
            select(Locomotive)
            .where(Locomotive.status == status)
            .order_by(Locomotive.code)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, locomotive: Locomotive) -> None:
        self._session.add(locomotive)

    async def delete(self, locomotive: Locomotive) -> None:
        await self._session.delete(locomotive)
