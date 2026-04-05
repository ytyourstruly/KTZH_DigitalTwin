from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.loco import TelemetryCurrent, TelemetrySnapshot
from app.repositories.protocols import TelemetryCurrentRepository, TelemetrySnapshotRepository


class TelemetryService:
    """Current row + snapshot history (``telemetry_current``, ``telemetry_snapshots``)."""

    __slots__ = ("_current", "_snapshots")

    def __init__(
        self,
        current: TelemetryCurrentRepository,
        snapshots: TelemetrySnapshotRepository,
    ) -> None:
        self._current = current
        self._snapshots = snapshots

    async def get_current(self, locomotive_id: UUID) -> TelemetryCurrent | None:
        return await self._current.get_by_locomotive_id(locomotive_id)

    async def require_current(self, locomotive_id: UUID) -> TelemetryCurrent:
        row = await self.get_current(locomotive_id)
        if row is None:
            raise NotFoundError("Telemetry current row not found", code="telemetry_current_not_found")
        return row

    async def save_current(self, row: TelemetryCurrent) -> None:
        await self._current.add(row)

    async def delete_current(self, row: TelemetryCurrent) -> None:
        await self._current.delete(row)

    async def get_snapshot(self, snapshot_id: int) -> TelemetrySnapshot | None:
        return await self._snapshots.get_by_id(snapshot_id)

    async def require_snapshot(self, snapshot_id: int) -> TelemetrySnapshot:
        snap = await self.get_snapshot(snapshot_id)
        if snap is None:
            raise NotFoundError("Telemetry snapshot not found", code="telemetry_snapshot_not_found")
        return snap

    async def list_snapshots_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TelemetrySnapshot]:
        return await self._snapshots.list_for_locomotive(
            locomotive_id, limit=limit, offset=offset
        )

    async def append_snapshot(self, snapshot: TelemetrySnapshot) -> None:
        await self._snapshots.add(snapshot)

    async def remove_snapshot(self, snapshot: TelemetrySnapshot) -> None:
        await self._snapshots.delete(snapshot)
