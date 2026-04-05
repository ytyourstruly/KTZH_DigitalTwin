from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.loco import TelemetryCurrent
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyTelemetryCurrentRepository(SqlAlchemyRepository):
    """``loco.telemetry_current`` — :class:`~app.repositories.protocols.TelemetryCurrentRepository`."""

    async def get_by_locomotive_id(self, locomotive_id: UUID) -> TelemetryCurrent | None:
        result = await self._session.execute(
            select(TelemetryCurrent).where(TelemetryCurrent.locomotive_id == locomotive_id)
        )
        return result.scalar_one_or_none()

    async def add(self, row: TelemetryCurrent) -> None:
        self._session.add(row)

    async def delete(self, row: TelemetryCurrent) -> None:
        await self._session.delete(row)
