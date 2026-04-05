from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.loco import Locomotive, LocomotiveStatus
from app.repositories.protocols import LocomotiveRepository


class LocomotiveService:
    """Use-cases for ``loco.locomotives``."""

    __slots__ = ("_locomotives",)

    def __init__(self, locomotives: LocomotiveRepository) -> None:
        self._locomotives = locomotives

    async def get_by_id(self, locomotive_id: UUID) -> Locomotive | None:
        return await self._locomotives.get_by_id(locomotive_id)

    async def require_by_id(self, locomotive_id: UUID) -> Locomotive:
        loco = await self.get_by_id(locomotive_id)
        if loco is None:
            raise NotFoundError("Locomotive not found", code="locomotive_not_found")
        return loco

    async def get_by_code(self, code: str) -> Locomotive | None:
        return await self._locomotives.get_by_code(code)

    async def list_page(self, *, limit: int = 100, offset: int = 0) -> list[Locomotive]:
        return await self._locomotives.list_page(limit=limit, offset=offset)

    async def list_by_status(
        self,
        status: LocomotiveStatus,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Locomotive]:
        return await self._locomotives.list_by_status(status, limit=limit, offset=offset)

    async def create(self, locomotive: Locomotive) -> None:
        await self._locomotives.add(locomotive)

    async def remove(self, locomotive: Locomotive) -> None:
        await self._locomotives.delete(locomotive)
