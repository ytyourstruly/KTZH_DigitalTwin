from app.repositories.sqlalchemy.loco.alert_events import SqlAlchemyAlertEventRepository
from app.repositories.sqlalchemy.loco.fault_events import SqlAlchemyFaultEventRepository
from app.repositories.sqlalchemy.loco.health_factor_breakdown import (
    SqlAlchemyHealthFactorBreakdownRepository,
)
from app.repositories.sqlalchemy.loco.index_settings import SqlAlchemyIndexSettingsRepository
from app.repositories.sqlalchemy.loco.locomotives import SqlAlchemyLocomotiveRepository
from app.repositories.sqlalchemy.loco.telemetry_current import (
    SqlAlchemyTelemetryCurrentRepository,
)
from app.repositories.sqlalchemy.loco.telemetry_snapshots import (
    SqlAlchemyTelemetrySnapshotRepository,
)

__all__ = [
    "SqlAlchemyAlertEventRepository",
    "SqlAlchemyFaultEventRepository",
    "SqlAlchemyHealthFactorBreakdownRepository",
    "SqlAlchemyIndexSettingsRepository",
    "SqlAlchemyLocomotiveRepository",
    "SqlAlchemyTelemetryCurrentRepository",
    "SqlAlchemyTelemetrySnapshotRepository",
]
