from __future__ import annotations

from app.models.auth import AuditLog
from app.repositories.protocols import AuditLogRepository


class AuditLogService:
    """Append-only audit trail (``auth.audit_log``)."""

    __slots__ = ("_audit",)

    def __init__(self, audit: AuditLogRepository) -> None:
        self._audit = audit

    async def record(self, entry: AuditLog) -> None:
        await self._audit.add(entry)
