from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.loco import TelemetrySnapshot
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyTelemetrySnapshotRepository(SqlAlchemyRepository):
    """``loco.telemetry_snapshots`` — :class:`~app.repositories.protocols.TelemetrySnapshotRepository`."""

    async def get_by_id(self, snapshot_id: int) -> TelemetrySnapshot | None:
        result = await self._session.execute(
            select(TelemetrySnapshot).where(TelemetrySnapshot.id == snapshot_id)
        )
        return result.scalar_one_or_none()

    async def list_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TelemetrySnapshot]:
        stmt = (
            select(TelemetrySnapshot)
            .where(TelemetrySnapshot.locomotive_id == locomotive_id)
            .order_by(TelemetrySnapshot.ts.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, snapshot: TelemetrySnapshot) -> None:
        self._session.add(snapshot)

    async def delete(self, snapshot: TelemetrySnapshot) -> None:
        await self._session.delete(snapshot)
