from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.loco import AlertEvent
from app.repositories.protocols import AlertEventRepository


class AlertEventService:
    """Use-cases for ``loco.alert_events``."""

    __slots__ = ("_alerts",)

    def __init__(self, alerts: AlertEventRepository) -> None:
        self._alerts = alerts

    async def get_by_id(self, event_id: int) -> AlertEvent | None:
        return await self._alerts.get_by_id(event_id)

    async def require_by_id(self, event_id: int) -> AlertEvent:
        row = await self.get_by_id(event_id)
        if row is None:
            raise NotFoundError("Alert event not found", code="alert_event_not_found")
        return row

    async def list_active_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
    ) -> list[AlertEvent]:
        return await self._alerts.list_active_for_locomotive(locomotive_id, limit=limit)

    async def raise_alert(self, event: AlertEvent) -> None:
        await self._alerts.add(event)

    async def remove(self, event: AlertEvent) -> None:
        await self._alerts.delete(event)
