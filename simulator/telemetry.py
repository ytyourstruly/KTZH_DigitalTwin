"""
telemetry.py — Pydantic models and value-range constants for locomotive telemetry.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Simulation mode enum
# ---------------------------------------------------------------------------

class SimMode(str, Enum):
    NORMAL      = "normal"
    DEGRADATION = "degradation"
    SPIKE       = "spike"
    FAILURE     = "failure"


# ---------------------------------------------------------------------------
# Realistic value ranges  (min, max, typical_centre)
# ---------------------------------------------------------------------------

RANGES = {
    # km/h
    "speed":       dict(min=0,    max=140,  centre=85,  sigma=5),
    # percent
    "fuel_level":  dict(min=0,    max=100,  centre=72,  sigma=1),
    # Celsius
    "engine_temp": dict(min=60,   max=120,  centre=88,  sigma=2),
    # bar
    "oil_pressure":dict(min=1.5,  max=6.0,  centre=3.8, sigma=0.1),
    # Volts
    "voltage":     dict(min=22.0, max=30.0, centre=27.5,sigma=0.2),
    # Amperes
    "current":     dict(min=100,  max=800,  centre=420, sigma=15),
}

# Possible error codes the simulator can emit
ALL_ERROR_CODES = [
    "E001_OVERHEAT",
    "E002_LOW_OIL",
    "E003_LOW_FUEL",
    "E004_VOLTAGE_DROP",
    "E005_OVERCURRENT",
    "E006_SENSOR_FAULT",
    "E007_BRAKE_PRESSURE",
    "E008_COOLANT_LEAK",
    "E009_TRACTION_LOSS",
    "E010_COMM_TIMEOUT",
]


# ---------------------------------------------------------------------------
# Telemetry message model
# ---------------------------------------------------------------------------

class TelemetryMessage(BaseModel):
    timestamp:      str
    locomotive_id:  str
    speed:          Optional[float] = Field(None, ge=0, le=200)
    fuel_level:     Optional[float] = Field(None, ge=0, le=100)
    engine_temp:    Optional[float] = Field(None, ge=0, le=200)
    oil_pressure:   Optional[float] = Field(None, ge=0, le=10)
    voltage:        Optional[float] = Field(None, ge=0, le=60)
    current:        Optional[float] = Field(None, ge=0, le=1500)
    error_codes:    Optional[list[str]] = []
    health_hint:    Optional[str] = "ok"
    mode:           Optional[str] = SimMode.NORMAL


# ---------------------------------------------------------------------------
# Control API models
# ---------------------------------------------------------------------------

class ModeRequest(BaseModel):
    mode: SimMode

class RateRequest(BaseModel):
    interval_ms: int = Field(..., ge=50, le=10_000,
                             description="Message interval in milliseconds")

class StatusResponse(BaseModel):
    mode:           str
    interval_ms:    int
    burst_active:   bool
    connected_clients: int
    messages_sent:  int
    uptime_seconds: float