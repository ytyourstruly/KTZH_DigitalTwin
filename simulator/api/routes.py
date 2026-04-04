"""
routes.py — HTTP control endpoints for the simulator.

POST /mode        → manually set simulation mode
GET  /status      → current mode + stats
POST /rate        → change message frequency
POST /burst       → enable/disable burst mode
POST /reset       → reset to normal
POST /fault       → toggle fault injection settings
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from telemetry import SimMode, ModeRequest, RateRequest, StatusResponse
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


@router.post("/rate", summary="Change message frequency")
async def set_rate(req: RateRequest):
    """
    Set the base interval between telemetry messages (50–10 000 ms).
    Burst mode overrides this with interval / burst_multiplier.
    """
    _b().set_interval(req.interval_ms)
    return {"ok": True, "interval_ms": req.interval_ms}


@router.post("/reset", summary="Reset simulator to normal mode")
async def reset():
    """Snap all parameters back to nominal values and enter NORMAL mode."""
    _b().reset()
    return {"ok": True, "mode": "normal"}


class BurstRequest(BaseModel):
    active: bool

@router.post("/burst", summary="Toggle burst (high-load) mode")
async def set_burst(req: BurstRequest):
    """
    Enable burst mode to simulate 10× message rate.
    Useful for high-load testing of the backend.
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