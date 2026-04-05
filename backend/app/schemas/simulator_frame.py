"""Payload shape emitted by the hackathon locomotive simulator WebSocket."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SimulatorFrame(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: str
    locomotive_id: str
    speed: float | None = None
    fuel_level: float | None = None
    engine_temp: float | None = None
    oil_pressure: float | None = None
    voltage: float | None = None
    current: float | None = None
    error_codes: list[str] = Field(default_factory=list)
    health_hint: str | None = "ok"
    mode: str | None = None
