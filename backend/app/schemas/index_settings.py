from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IndexSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metric_name: str
    min_normal: float | None
    max_normal: float | None
    warning_threshold: float | None
    critical_threshold: float | None
    weight: float = Field(..., ge=0.0, le=1.0)
    enabled: bool
    updated_at: datetime
    updated_by: UUID | None


class IndexSettingPatch(BaseModel):
    """Частичное обновление строки (только админ)."""

    model_config = ConfigDict(extra="forbid")

    min_normal: float | None = None
    max_normal: float | None = None
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    weight: float | None = Field(default=None, ge=0.0, le=1.0)
    enabled: bool | None = None
