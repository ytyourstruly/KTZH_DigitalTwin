from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.loco import HealthFactorBreakdown
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyHealthFactorBreakdownRepository(SqlAlchemyRepository):
    """``loco.health_factor_breakdown`` — :class:`~app.repositories.protocols.HealthFactorBreakdownRepository`."""

    async def get_by_id(self, row_id: int) -> HealthFactorBreakdown | None:
        result = await self._session.execute(
            select(HealthFactorBreakdown).where(HealthFactorBreakdown.id == row_id)
        )
        return result.scalar_one_or_none()

    async def list_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[HealthFactorBreakdown]:
        stmt = (
            select(HealthFactorBreakdown)
            .where(HealthFactorBreakdown.locomotive_id == locomotive_id)
            .order_by(HealthFactorBreakdown.ts.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, row: HealthFactorBreakdown) -> None:
        self._session.add(row)

    async def delete(self, row: HealthFactorBreakdown) -> None:
        await self._session.delete(row)
