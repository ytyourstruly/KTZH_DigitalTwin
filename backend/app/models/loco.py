from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.models.auth import User

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    desc,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

LOCO_SCHEMA = "loco"
AUTH_SCHEMA = "auth"


class HealthStatus(str, enum.Enum):
    normal = "normal"
    attention = "attention"
    critical = "critical"
    unknown = "unknown"


class LocomotiveStatus(str, enum.Enum):
    active = "active"
    maintenance = "maintenance"
    idle = "idle"
    decommissioned = "decommissioned"


class Severity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


_health_status = Enum(
    HealthStatus,
    name="health_status_enum",
    schema=LOCO_SCHEMA,
    native_enum=True,
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)
_locomotive_status = Enum(
    LocomotiveStatus,
    name="locomotive_status",
    schema=LOCO_SCHEMA,
    native_enum=True,
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)
_severity = Enum(
    Severity,
    name="severity_enum",
    schema=LOCO_SCHEMA,
    native_enum=True,
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)


class Locomotive(Base):
    __tablename__ = "locomotives"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[LocomotiveStatus] = mapped_column(
        _locomotive_status,
        nullable=False,
        server_default=text("'idle'::loco.locomotive_status"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    telemetry_current: Mapped[TelemetryCurrent | None] = relationship(
        back_populates="locomotive",
        uselist=False,
        cascade="all, delete-orphan",
    )
    telemetry_snapshots: Mapped[list[TelemetrySnapshot]] = relationship(
        back_populates="locomotive",
        cascade="all, delete-orphan",
    )
    alert_events: Mapped[list[AlertEvent]] = relationship(
        back_populates="locomotive",
        cascade="all, delete-orphan",
    )
    fault_events: Mapped[list[FaultEvent]] = relationship(
        back_populates="locomotive",
        cascade="all, delete-orphan",
    )
    health_factor_breakdowns: Mapped[list[HealthFactorBreakdown]] = relationship(
        back_populates="locomotive",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_locomotives_code", "code"),
        Index("idx_locomotives_status", "status"),
        {"schema": LOCO_SCHEMA},
    )


class TelemetryCurrent(Base):
    __tablename__ = "telemetry_current"
    __table_args__ = (
        CheckConstraint(
            "health_index >= 0 AND health_index <= 100",
            name="telemetry_current_health_index_check",
        ),
        CheckConstraint(
            "signal_quality >= 0 AND signal_quality <= 100",
            name="telemetry_current_signal_quality_check",
        ),
        {"schema": LOCO_SCHEMA},
    )

    locomotive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{LOCO_SCHEMA}.locomotives.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    speed: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fuel_level: Mapped[float | None] = mapped_column(Numeric(5, 2))
    battery_voltage: Mapped[float | None] = mapped_column(Numeric(6, 2))
    traction_current: Mapped[float | None] = mapped_column(Numeric(7, 2))
    brake_pressure: Mapped[float | None] = mapped_column(Numeric(6, 2))
    engine_temp: Mapped[float | None] = mapped_column(Numeric(6, 2))
    vibration_level: Mapped[float | None] = mapped_column(Numeric(6, 3))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    signal_quality: Mapped[int | None] = mapped_column(SmallInteger)
    health_index: Mapped[float | None] = mapped_column(Numeric(5, 2))
    health_status: Mapped[HealthStatus] = mapped_column(
        _health_status,
        nullable=False,
        server_default=text("'unknown'::loco.health_status_enum"),
    )

    locomotive: Mapped[Locomotive] = relationship(back_populates="telemetry_current")


class TelemetrySnapshot(Base):
    __tablename__ = "telemetry_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    locomotive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{LOCO_SCHEMA}.locomotives.id", ondelete="CASCADE"),
        nullable=False,
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    speed: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fuel_level: Mapped[float | None] = mapped_column(Numeric(5, 2))
    battery_voltage: Mapped[float | None] = mapped_column(Numeric(6, 2))
    traction_current: Mapped[float | None] = mapped_column(Numeric(7, 2))
    brake_pressure: Mapped[float | None] = mapped_column(Numeric(6, 2))
    engine_temp: Mapped[float | None] = mapped_column(Numeric(6, 2))
    vibration_level: Mapped[float | None] = mapped_column(Numeric(6, 3))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    signal_quality: Mapped[int | None] = mapped_column(SmallInteger)
    health_index: Mapped[float | None] = mapped_column(Numeric(5, 2))
    health_status: Mapped[HealthStatus] = mapped_column(
        _health_status,
        nullable=False,
        server_default=text("'unknown'::loco.health_status_enum"),
    )

    locomotive: Mapped[Locomotive] = relationship(back_populates="telemetry_snapshots")
    health_factor_breakdowns: Mapped[list[HealthFactorBreakdown]] = relationship(
        back_populates="snapshot",
    )

    __table_args__ = (
        CheckConstraint(
            "health_index >= 0 AND health_index <= 100",
            name="telemetry_snapshots_health_index_check",
        ),
        CheckConstraint(
            "signal_quality >= 0 AND signal_quality <= 100",
            name="telemetry_snapshots_signal_quality_check",
        ),
        Index("idx_ts_snapshots_loco_ts", locomotive_id, desc(ts)),
        Index("idx_ts_snapshots_ts", desc(ts)),
        {"schema": LOCO_SCHEMA},
    )


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    locomotive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{LOCO_SCHEMA}.locomotives.id", ondelete="CASCADE"),
        nullable=False,
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[Severity] = mapped_column(_severity, nullable=False)
    source_metric: Mapped[str | None] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(12, 4))
    threshold_value: Mapped[float | None] = mapped_column(Numeric(12, 4))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    locomotive: Mapped[Locomotive] = relationship(back_populates="alert_events")

    __table_args__ = (
        Index(
            "idx_alert_events_active",
            "locomotive_id",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
        Index("idx_alert_events_loco_ts", locomotive_id, desc(ts)),
        {"schema": LOCO_SCHEMA},
    )


class FaultEvent(Base):
    __tablename__ = "fault_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    locomotive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{LOCO_SCHEMA}.locomotives.id", ondelete="CASCADE"),
        nullable=False,
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fault_code: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[Severity] = mapped_column(_severity, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    locomotive: Mapped[Locomotive] = relationship(back_populates="fault_events")

    __table_args__ = (
        Index(
            "idx_fault_events_active",
            "locomotive_id",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
        Index("idx_fault_events_code", "fault_code"),
        Index("idx_fault_events_loco_ts", locomotive_id, desc(ts)),
        {"schema": LOCO_SCHEMA},
    )


class HealthFactorBreakdown(Base):
    __tablename__ = "health_factor_breakdown"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    locomotive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{LOCO_SCHEMA}.locomotives.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(f"{LOCO_SCHEMA}.telemetry_snapshots.id", ondelete="SET NULL"),
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Numeric(12, 4))
    contribution_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    weight: Mapped[float | None] = mapped_column(Numeric(5, 4))
    reason_text: Mapped[str | None] = mapped_column(Text)

    locomotive: Mapped[Locomotive] = relationship(back_populates="health_factor_breakdowns")
    snapshot: Mapped[TelemetrySnapshot | None] = relationship(
        back_populates="health_factor_breakdowns",
    )

    __table_args__ = (
        Index("idx_hfb_loco_ts", locomotive_id, desc(ts)),
        Index("idx_hfb_snapshot_id", "snapshot_id"),
        {"schema": LOCO_SCHEMA},
    )


class IndexSettings(Base):
    __tablename__ = "index_settings"
    __table_args__ = (
        CheckConstraint(
            "weight >= 0 AND weight <= 1",
            name="index_settings_weight_check",
        ),
        {"schema": LOCO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    min_normal: Mapped[float | None] = mapped_column(Numeric(12, 4))
    max_normal: Mapped[float | None] = mapped_column(Numeric(12, 4))
    warning_threshold: Mapped[float | None] = mapped_column(Numeric(12, 4))
    critical_threshold: Mapped[float | None] = mapped_column(Numeric(12, 4))
    weight: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("1.0")
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{AUTH_SCHEMA}.users.id", ondelete="SET NULL"),
    )

    updated_by_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[updated_by],
    )
