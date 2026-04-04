"""Map simulator WebSocket frames to ``loco`` tables (current + optional snapshot)."""

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


def _parse_ts(iso: str) -> datetime:
    s = iso.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _hint_to_score(hint: str | None) -> tuple[float, HealthStatus]:
    h = (hint or "ok").lower()
    if h == "critical":
        return 28.0, HealthStatus.critical
    if h in ("warning_high", "spike"):
        return 55.0, HealthStatus.attention
    if h in ("warning_low", "degrading", "glitch"):
        return 72.0, HealthStatus.attention
    return 92.0, HealthStatus.normal


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


async def apply_simulator_frame(
    provider: ServiceProvider,
    frame: SimulatorFrame,
    *,
    write_snapshot: bool,
) -> dict[str, Any]:
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

    health_index, health_status = _hint_to_score(frame.health_hint)

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

    return {
        "timestamp": frame.timestamp,
        "locomotive_id": frame.locomotive_id,
        "locomotive_uuid": str(loco.id),
        "speed": frame.speed,
        "fuel_level": frame.fuel_level,
        "engine_temp": frame.engine_temp,
        "oil_pressure": frame.oil_pressure,
        "voltage": frame.voltage,
        "current": frame.current,
        "error_codes": frame.error_codes,
        "health_hint": frame.health_hint,
        "health_index": health_index,
        "health_status": health_status.value,
        "mode": frame.mode,
    }
