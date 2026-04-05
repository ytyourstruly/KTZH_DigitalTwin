"""Wires SQLAlchemy repositories and application services for one :class:`AsyncSession` / request."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.repositories.sqlalchemy import (
    SqlAlchemyAlertEventRepository,
    SqlAlchemyAuditLogRepository,
    SqlAlchemyAuthSessionRepository,
    SqlAlchemyFaultEventRepository,
    SqlAlchemyHealthFactorBreakdownRepository,
    SqlAlchemyIndexSettingsRepository,
    SqlAlchemyLocomotiveRepository,
    SqlAlchemyTelemetryCurrentRepository,
    SqlAlchemyTelemetrySnapshotRepository,
    SqlAlchemyUserRepository,
)
from app.services.auth import (
    AuditLogService,
    AuthSessionService,
    AuthenticationService,
    UserService,
)
from app.services.loco import (
    AlertEventService,
    FaultEventService,
    HealthFactorBreakdownService,
    IndexSettingsService,
    LocomotiveService,
    TelemetryService,
)


class ServiceProvider:
    """One provider per unit of work (typically one FastAPI request via :func:`get_session`)."""

    __slots__ = (
        "_session",
        "_user_repo",
        "_auth_session_repo",
        "_audit_log_repo",
        "_locomotive_repo",
        "_telemetry_current_repo",
        "_telemetry_snapshot_repo",
        "_alert_event_repo",
        "_fault_event_repo",
        "_health_factor_repo",
        "_index_settings_repo",
        "_authentication_service",
    )

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = SqlAlchemyUserRepository(session)
        self._auth_session_repo = SqlAlchemyAuthSessionRepository(session)
        self._audit_log_repo = SqlAlchemyAuditLogRepository(session)
        self._locomotive_repo = SqlAlchemyLocomotiveRepository(session)
        self._telemetry_current_repo = SqlAlchemyTelemetryCurrentRepository(session)
        self._telemetry_snapshot_repo = SqlAlchemyTelemetrySnapshotRepository(session)
        self._alert_event_repo = SqlAlchemyAlertEventRepository(session)
        self._fault_event_repo = SqlAlchemyFaultEventRepository(session)
        self._health_factor_repo = SqlAlchemyHealthFactorBreakdownRepository(session)
        self._index_settings_repo = SqlAlchemyIndexSettingsRepository(session)

    @property
    def session(self) -> AsyncSession:
        return self._session

    def user_service(self) -> UserService:
        return UserService(self._user_repo)

    def authentication_service(self) -> AuthenticationService:
        return AuthenticationService(
            users=self.user_service(),
            sessions=self.auth_session_service(),
            session_ttl_hours=get_settings().session_ttl_hours,
        )

    def auth_session_service(self) -> AuthSessionService:
        return AuthSessionService(self._auth_session_repo)

    def audit_log_service(self) -> AuditLogService:
        return AuditLogService(self._audit_log_repo)

    def locomotive_service(self) -> LocomotiveService:
        return LocomotiveService(self._locomotive_repo)

    def telemetry_service(self) -> TelemetryService:
        return TelemetryService(self._telemetry_current_repo, self._telemetry_snapshot_repo)

    def alert_event_service(self) -> AlertEventService:
        return AlertEventService(self._alert_event_repo)

    def fault_event_service(self) -> FaultEventService:
        return FaultEventService(self._fault_event_repo)

    def health_factor_breakdown_service(self) -> HealthFactorBreakdownService:
        return HealthFactorBreakdownService(self._health_factor_repo)

    def index_settings_service(self) -> IndexSettingsService:
        return IndexSettingsService(self._index_settings_repo)
