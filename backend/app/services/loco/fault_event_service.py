from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.loco import FaultEvent
from app.repositories.protocols import FaultEventRepository


class FaultEventService:
    """Use-cases for ``loco.fault_events``."""

    __slots__ = ("_faults",)

    def __init__(self, faults: FaultEventRepository) -> None:
        self._faults = faults

    async def get_by_id(self, event_id: int) -> FaultEvent | None:
        return await self._faults.get_by_id(event_id)

    async def require_by_id(self, event_id: int) -> FaultEvent:
        row = await self.get_by_id(event_id)
        if row is None:
            raise NotFoundError("Fault event not found", code="fault_event_not_found")
        return row

    async def list_active_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
    ) -> list[FaultEvent]:
        return await self._faults.list_active_for_locomotive(locomotive_id, limit=limit)

    async def record(self, event: FaultEvent) -> None:
        await self._faults.add(event)

    async def remove(self, event: FaultEvent) -> None:
        await self._faults.delete(event)
