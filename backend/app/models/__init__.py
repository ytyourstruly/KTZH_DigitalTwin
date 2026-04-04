# Import order: auth before loco (cross-schema FK from loco.index_settings to auth.users).
from app.models.auth import AuditLog, AuthSession, User, UserRole  # noqa: F401
from app.models.loco import (  # noqa: F401
    AlertEvent,
    FaultEvent,
    HealthFactorBreakdown,
    HealthStatus,
    IndexSettings,
    Locomotive,
    LocomotiveStatus,
    Severity,
    TelemetryCurrent,
    TelemetrySnapshot,
)
