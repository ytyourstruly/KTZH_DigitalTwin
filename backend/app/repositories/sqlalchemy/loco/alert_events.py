from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.loco import AlertEvent
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyAlertEventRepository(SqlAlchemyRepository):
    """``loco.alert_events`` — :class:`~app.repositories.protocols.AlertEventRepository`."""

    async def get_by_id(self, event_id: int) -> AlertEvent | None:
        result = await self._session.execute(
            select(AlertEvent).where(AlertEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def list_active_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
    ) -> list[AlertEvent]:
        stmt = (
            select(AlertEvent)
            .where(
                AlertEvent.locomotive_id == locomotive_id,
                AlertEvent.is_active.is_(True),
            )
            .order_by(AlertEvent.ts.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, event: AlertEvent) -> None:
        self._session.add(event)

    async def delete(self, event: AlertEvent) -> None:
        await self._session.delete(event)
