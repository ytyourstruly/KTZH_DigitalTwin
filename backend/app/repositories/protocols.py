"""Persistence contracts (ports). **Use :class:`typing.Protocol` here**, not ABCs.

Why Protocol
------------
Services and FastAPI dependencies depend on *capabilities* (methods), not on a
shared base class. Fakes and alternate backends implement the same methods;
type checkers enforce the shape. ABCs are better when you share *code* in a
base class or want instantiation to fail unless every ``@abstractmethod`` is
overridden.

Implementations live under ``app.repositories.sqlalchemy.auth`` and
``.loco`` (one module per port). Shared :class:`~app.repositories.sqlalchemy.base.SqlAlchemyRepository` holds ``_session``.

Tables ↔ protocols (see ``app.models``)
---------------------------------------
``auth.users``              → :class:`UserRepository`
``auth.sessions``           → :class:`AuthSessionRepository`
``auth.audit_log``          → :class:`AuditLogRepository`
``loco.locomotives``        → :class:`LocomotiveRepository`
``loco.telemetry_current``  → :class:`TelemetryCurrentRepository`
``loco.telemetry_snapshots``→ :class:`TelemetrySnapshotRepository`
``loco.alert_events``       → :class:`AlertEventRepository`
``loco.fault_events``       → :class:`FaultEventRepository`
``loco.health_factor_breakdown`` → :class:`HealthFactorBreakdownRepository`
``loco.index_settings``     → :class:`IndexSettingsRepository`

Generic CRUD
------------
A generic ``AsyncCrudRepository[T, Id]`` is *optional*. It reduces duplication
when many entities share identical ``get_by_id`` / ``add`` / ``delete`` shapes,
but it also encourages “one size fits all” APIs that fight domain-specific
queries (``get_by_email``, partial indexes, etc.). Here we keep **per-table
protocols** as the source of truth; use :class:`AsyncCrudRepository` only as a
mixin-style hint for new entities that truly match.

**Updates:** for SQLAlchemy, load the instance, mutate attributes, flush—no
separate ``update`` method is required unless you want explicit commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from uuid import UUID

if TYPE_CHECKING:
    from app.models.auth import AuditLog, AuthSession, User
    from app.models.loco import (
        AlertEvent,
        FaultEvent,
        HealthFactorBreakdown,
        IndexSettings,
        Locomotive,
        LocomotiveStatus,
        TelemetryCurrent,
        TelemetrySnapshot,
    )

T = TypeVar("T")
Id = TypeVar("Id")


class AsyncCrudRepository(Protocol[T, Id]):
    """Optional generic port when an entity really is plain CRUD by a single id."""

    async def get_by_id(self, entity_id: Id) -> T | None: ...

    async def add(self, entity: T) -> None: ...

    async def delete(self, entity: T) -> None: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None: ...

    async def add(self, user: User) -> None: ...

    async def delete(self, user: User) -> None: ...


class AuthSessionRepository(Protocol):
    async def get_by_id(self, session_id: UUID) -> AuthSession | None: ...

    async def get_by_token_hash(self, token_hash: str) -> AuthSession | None: ...

    async def add(self, session: AuthSession) -> None: ...

    async def delete(self, session: AuthSession) -> None: ...


class AuditLogRepository(Protocol):
    async def add(self, entry: AuditLog) -> None: ...


class LocomotiveRepository(Protocol):
    async def get_by_id(self, locomotive_id: UUID) -> Locomotive | None: ...

    async def get_by_code(self, code: str) -> Locomotive | None: ...

    async def list_page(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Locomotive]: ...

    async def list_by_status(
        self,
        status: LocomotiveStatus,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Locomotive]: ...

    async def add(self, locomotive: Locomotive) -> None: ...

    async def delete(self, locomotive: Locomotive) -> None: ...


class TelemetryCurrentRepository(Protocol):
    async def get_by_locomotive_id(self, locomotive_id: UUID) -> TelemetryCurrent | None: ...

    async def add(self, row: TelemetryCurrent) -> None: ...

    async def delete(self, row: TelemetryCurrent) -> None: ...


class TelemetrySnapshotRepository(Protocol):
    async def get_by_id(self, snapshot_id: int) -> TelemetrySnapshot | None: ...

    async def list_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TelemetrySnapshot]: ...

    async def add(self, snapshot: TelemetrySnapshot) -> None: ...

    async def delete(self, snapshot: TelemetrySnapshot) -> None: ...


class AlertEventRepository(Protocol):
    async def get_by_id(self, event_id: int) -> AlertEvent | None: ...

    async def list_active_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
    ) -> list[AlertEvent]: ...

    async def add(self, event: AlertEvent) -> None: ...

    async def delete(self, event: AlertEvent) -> None: ...


class FaultEventRepository(Protocol):
    async def get_by_id(self, event_id: int) -> FaultEvent | None: ...

    async def list_active_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
    ) -> list[FaultEvent]: ...

    async def add(self, event: FaultEvent) -> None: ...

    async def delete(self, event: FaultEvent) -> None: ...


class HealthFactorBreakdownRepository(Protocol):
    async def get_by_id(self, row_id: int) -> HealthFactorBreakdown | None: ...

    async def list_for_locomotive(
        self,
        locomotive_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[HealthFactorBreakdown]: ...

    async def add(self, row: HealthFactorBreakdown) -> None: ...

    async def delete(self, row: HealthFactorBreakdown) -> None: ...


class IndexSettingsRepository(Protocol):
    async def get_by_id(self, settings_id: int) -> IndexSettings | None: ...

    async def get_by_metric_name(self, metric_name: str) -> IndexSettings | None: ...

    async def list_all(self) -> list[IndexSettings]: ...

    async def add(self, row: IndexSettings) -> None: ...

    async def delete(self, row: IndexSettings) -> None: ...
