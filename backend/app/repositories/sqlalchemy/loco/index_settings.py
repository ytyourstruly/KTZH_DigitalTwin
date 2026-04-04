from __future__ import annotations

from sqlalchemy import select

from app.models.loco import IndexSettings
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyIndexSettingsRepository(SqlAlchemyRepository):
    """``loco.index_settings`` — :class:`~app.repositories.protocols.IndexSettingsRepository`."""

    async def get_by_id(self, settings_id: int) -> IndexSettings | None:
        result = await self._session.execute(
            select(IndexSettings).where(IndexSettings.id == settings_id)
        )
        return result.scalar_one_or_none()

    async def get_by_metric_name(self, metric_name: str) -> IndexSettings | None:
        result = await self._session.execute(
            select(IndexSettings).where(IndexSettings.metric_name == metric_name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[IndexSettings]:
        stmt = select(IndexSettings).order_by(IndexSettings.metric_name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, row: IndexSettings) -> None:
        self._session.add(row)

    async def delete(self, row: IndexSettings) -> None:
        await self._session.delete(row)
