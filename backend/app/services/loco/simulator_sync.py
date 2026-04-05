"""Persist simulator frames to ``loco`` tables using precomputed live view (see ``telemetry_live_view``)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.loco import (
    HealthStatus,
    Locomotive,
    LocomotiveStatus,
    TelemetryCurrent,
    TelemetrySnapshot,
)
from app.provider.service_provider import ServiceProvider
from app.schemas.simulator_frame import SimulatorFrame
from app.services.loco.telemetry_live_view import remember_locomotive_uuid


def _parse_ts(iso: str) -> datetime:
    s = iso.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _health_status_from_live(value: str) -> HealthStatus:
    try:
        return HealthStatus(value)
    except ValueError:
        return HealthStatus.unknown


def _fill_telemetry_row(
    row: TelemetryCurrent | TelemetrySnapshot,
    *,
    ts: datetime,
    frame: SimulatorFrame,
    health_index: float,
    health_status: HealthStatus,
) -> None:
    row.ts = ts
    row.speed = frame.speed
    row.fuel_level = frame.fuel_level
    row.engine_temp = frame.engine_temp
    row.brake_pressure = frame.oil_pressure
    row.battery_voltage = frame.voltage
    row.traction_current = frame.current
    row.vibration_level = None
    row.latitude = None
    row.longitude = None
    row.signal_quality = None
    row.health_index = health_index
    row.health_status = health_status


async def persist_simulator_frame(
    provider: ServiceProvider,
    frame: SimulatorFrame,
    live: dict[str, Any],
    *,
    write_snapshot: bool,
) -> None:
    """Writes current row and optional snapshot; ``live`` is the payload already sent to clients."""
    loco_svc = provider.locomotive_service()
    tel_svc = provider.telemetry_service()
    ts = _parse_ts(frame.timestamp)

    loco = await loco_svc.get_by_code(frame.locomotive_id)
    if loco is None:
        loco = Locomotive(
            code=frame.locomotive_id,
            model="SIM",
            name=frame.locomotive_id,
            status=LocomotiveStatus.active,
        )
        await loco_svc.create(loco)
        await provider.session.flush()

    health_index = float(live["health_index"])
    health_status = _health_status_from_live(str(live["health_status"]))

    cur = await tel_svc.get_current(loco.id)
    if cur is None:
        cur = TelemetryCurrent(locomotive_id=loco.id)
        _fill_telemetry_row(
            cur,
            ts=ts,
            frame=frame,
            health_index=health_index,
            health_status=health_status,
        )
        await tel_svc.save_current(cur)
    else:
        _fill_telemetry_row(
            cur,
            ts=ts,
            frame=frame,
            health_index=health_index,
            health_status=health_status,
        )

    if write_snapshot:
        snap = TelemetrySnapshot(locomotive_id=loco.id)
        _fill_telemetry_row(
            snap,
            ts=ts,
            frame=frame,
            health_index=health_index,
            health_status=health_status,
        )
        await tel_svc.append_snapshot(snap)

    remember_locomotive_uuid(frame.locomotive_id, str(loco.id))
