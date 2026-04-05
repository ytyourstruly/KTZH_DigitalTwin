"""
routes.py — HTTP control endpoints for the simulator.

POST /mode        → manually set simulation mode
GET  /status      → current mode + stats (now includes Hz fields)
POST /rate        → change message frequency (raw ms, backwards-compat)
POST /frequency   → set frequency by named preset (normal / highload / burst)
POST /burst       → legacy burst toggle (delegates to /frequency)
POST /reset       → reset to normal
POST /fault       → toggle fault injection settings
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from telemetry import (
    SimMode, FrequencyPreset,
    ModeRequest, RateRequest, FrequencyRequest, StatusResponse,
)
from broadcaster import Broadcaster

router = APIRouter()
_broadcaster: Broadcaster | None = None


def register(broadcaster: Broadcaster) -> None:
    """Called from main.py to inject the shared broadcaster instance."""
    global _broadcaster
    _broadcaster = broadcaster


def _b() -> Broadcaster:
    assert _broadcaster is not None, "Broadcaster not registered"
    return _broadcaster


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/mode", summary="Set simulation mode")
async def set_mode(req: ModeRequest):
    """
    Switch the simulator to one of:
    - `normal`      — stable, realistic values
    - `degradation` — parameters slowly worsen over time
    - `spike`       — sudden random anomaly bursts
    - `failure`     — critical values + multiple error codes
    """
    _b().set_mode(req.mode)
    return {"ok": True, "mode": req.mode}


@router.get("/status", response_model=StatusResponse, summary="Simulator status")
async def get_status():
    """Return current mode, interval, client count, and uptime."""
    return _b().status


@router.post("/rate", summary="Change message interval (raw ms)")
async def set_rate(req: RateRequest):
    """
    Set the base interval between telemetry messages (20–10 000 ms).
    Use `/frequency` for the named Hz presets instead.
    """
    _b().set_interval(req.interval_ms)
    return {"ok": True, "interval_ms": req.interval_ms}


@router.post("/frequency", summary="Set frequency by named preset")
async def set_frequency(req: FrequencyRequest):
    """
    Switch message rate using a named preset:

    | Preset     | Rate    | Behaviour                                    |
    |------------|---------|----------------------------------------------|
    | `normal`   | 1 Hz    | 1 message/s — persistent                    |
    | `highload` | 10 Hz   | 10 messages/s — persistent                  |
    | `burst`    | 50 Hz   | 50 messages/s for **3 seconds**, then reverts to the previous preset |

    Burst is fire-and-forget — no need to manually cancel it.
    """
    result = _b().set_frequency(req.preset)
    return {"ok": True, **result}


@router.post("/reset", summary="Reset simulator to normal mode")
async def reset():
    """Snap all parameters back to nominal values, enter NORMAL mode, and set frequency to normal (1 Hz)."""
    _b().reset()
    return {"ok": True, "mode": "normal", "frequency_preset": "normal"}


class BurstRequest(BaseModel):
    active: bool

@router.post("/burst", summary="Toggle burst mode (legacy — prefer /frequency)")
async def set_burst(req: BurstRequest):
    """
    Legacy endpoint. Delegates to `/frequency`:
    - `active: true`  → preset=burst  (50 Hz / 3 s)
    - `active: false` → reverts to base preset
    """
    _b().set_burst(req.active)
    return {"ok": True, "burst_active": req.active}


class FaultRequest(BaseModel):
    random_disconnects:       bool | None = None
    missing_fields_enabled:   bool | None = None
    jitter_enabled:           bool | None = None

@router.post("/fault", summary="Toggle fault injection settings")
async def set_fault(req: FaultRequest):
    """
    Dynamically enable/disable fault injection:
    - `random_disconnects`     — forcibly drop client connections
    - `missing_fields_enabled` — randomly omit telemetry fields
    - `jitter_enabled`         — add random delay to messages
    """
    b = _b()
    changed = {}
    if req.random_disconnects is not None:
        b.random_disconnects = req.random_disconnects
        changed["random_disconnects"] = req.random_disconnects
    if req.missing_fields_enabled is not None:
        b.engine.missing_fields_enabled = req.missing_fields_enabled
        changed["missing_fields_enabled"] = req.missing_fields_enabled
    if req.jitter_enabled is not None:
        b.jitter_enabled = req.jitter_enabled
        changed["jitter_enabled"] = req.jitter_enabled
    return {"ok": True, "changed": changed}