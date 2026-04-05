from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.loco import HealthFactorBreakdown
from app.repositories.protocols import HealthFactorBreakdownRepository


class HealthFactorBreakdownService:
    """Explainability rows (``loco.health_factor_breakdown``)."""

    __slots__ = ("_factors",)

    def __init__(self, factors: HealthFactorBreakdownRepository) -> None:
        self._factors = factors

    async def get_by_id(self, row_id: int) -> HealthFactorBreakdown | None:
        return await self._factors.get_by_id(row_id)

    async def require_by_id(self, row_id: int) -> HealthFactorBreakdown:
        row = await self.get_by_id(row_id)
        if row is None:
            raise NotFoundError("Health factor row not found", code="health_factor_not_found")
        return row

    async def list_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[HealthFactorBreakdown]:
        return await self._factors.list_for_locomotive(
            locomotive_id, limit=limit, offset=offset
        )

    async def record(self, row: HealthFactorBreakdown) -> None:
        await self._factors.add(row)

    async def remove(self, row: HealthFactorBreakdown) -> None:
        await self._factors.delete(row)
