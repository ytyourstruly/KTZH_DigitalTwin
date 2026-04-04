from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.loco import IndexSettings
from app.repositories.protocols import IndexSettingsRepository
from app.schemas.index_settings import IndexSettingPatch


class IndexSettingsService:
    """Health-index thresholds and weights (``loco.index_settings``)."""

    __slots__ = ("_settings",)

    def __init__(self, settings: IndexSettingsRepository) -> None:
        self._settings = settings

    async def get_by_id(self, settings_id: int) -> IndexSettings | None:
        return await self._settings.get_by_id(settings_id)

    async def require_by_id(self, settings_id: int) -> IndexSettings:
        row = await self.get_by_id(settings_id)
        if row is None:
            raise NotFoundError("Index setting not found", code="index_settings_not_found")
        return row

    async def get_by_metric_name(self, metric_name: str) -> IndexSettings | None:
        return await self._settings.get_by_metric_name(metric_name)

    async def require_by_metric_name(self, metric_name: str) -> IndexSettings:
        row = await self.get_by_metric_name(metric_name)
        if row is None:
            raise NotFoundError("Index setting not found", code="index_settings_metric_not_found")
        return row

    async def list_all(self) -> list[IndexSettings]:
        return await self._settings.list_all()

    async def create(self, row: IndexSettings) -> None:
        await self._settings.add(row)

    async def remove(self, row: IndexSettings) -> None:
        await self._settings.delete(row)

    async def patch_by_metric_name(
        self,
        metric_name: str,
        body: IndexSettingPatch,
        *,
        updated_by: UUID,
    ) -> IndexSettings:
        row = await self.require_by_metric_name(metric_name)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        row.updated_by = updated_by
        row.updated_at = datetime.now(UTC)
        return row
