from __future__ import annotations

from app.models.auth import AuditLog
from app.repositories.sqlalchemy.base import SqlAlchemyRepository


class SqlAlchemyAuditLogRepository(SqlAlchemyRepository):
    """``auth.audit_log`` — :class:`~app.repositories.protocols.AuditLogRepository`."""

    async def add(self, entry: AuditLog) -> None:
        self._session.add(entry)
