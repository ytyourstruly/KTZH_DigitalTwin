"""Pydantic models for live telemetry (WebSocket + ``GET /telemetry/latest``)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MetricUiStatus = Literal["normal", "warning", "critical", "unknown"]
HealthStatusLiteral = Literal["normal", "attention", "critical"]
AlertSeverityLiteral = Literal["critical", "attention", "info"]
RecPriorityLiteral = Literal["high", "medium", "low"]


class TelemetryRawOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    speed: float | None = None
    fuel_level: float | None = None
    engine_temp: float | None = None
    oil_pressure: float | None = None
    voltage: float | None = None
    current: float | None = None


class MetricCardOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: float | None = None
    unit: str
    label_ru: str
    norm_min: float | None = None
    norm_max: float | None = None
    status: MetricUiStatus


class TopFactorOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    label: str
    impact_pct: float
    severity: MetricUiStatus


class AlertOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    severity: AlertSeverityLiteral
    subsystem: str
    message: str


class RecommendationOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    priority: RecPriorityLiteral
    urgency_ru: str
    action_ru: str
    reason_ru: str


class TelemetryLiveOut(BaseModel):
    """Снимок дашборда после расчёта порогов и индекса."""

    model_config = ConfigDict(extra="ignore")

    timestamp: str
    locomotive_id: str
    locomotive_uuid: str | None = None
    mode: str | None = None
    health_hint: str | None = None
    error_codes: list[str] = Field(default_factory=list)
    health_index: float
    health_status: HealthStatusLiteral
    raw: TelemetryRawOut
    metrics: dict[str, MetricCardOut]
    trends: dict[str, float | None] = Field(default_factory=dict)
    top_factors: list[TopFactorOut] = Field(default_factory=list)
    alerts: list[AlertOut] = Field(default_factory=list)
    recommendations: list[RecommendationOut] = Field(default_factory=list)
