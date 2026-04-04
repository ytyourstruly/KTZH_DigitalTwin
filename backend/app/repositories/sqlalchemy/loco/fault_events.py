from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.loco import FaultEvent
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyFaultEventRepository(SqlAlchemyRepository):
    """``loco.fault_events`` — :class:`~app.repositories.protocols.FaultEventRepository`."""

    async def get_by_id(self, event_id: int) -> FaultEvent | None:
        result = await self._session.execute(
            select(FaultEvent).where(FaultEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def list_active_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
    ) -> list[FaultEvent]:
        stmt = (
            select(FaultEvent)
            .where(
                FaultEvent.locomotive_id == locomotive_id,
                FaultEvent.is_active.is_(True),
            )
            .order_by(FaultEvent.ts.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, event: FaultEvent) -> None:
        self._session.add(event)

    async def delete(self, event: FaultEvent) -> None:
        await self._session.delete(event)
