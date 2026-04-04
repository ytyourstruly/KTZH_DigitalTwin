"""
Rule-based live dashboard view from a simulator frame: thresholds, health index, trends, factors.

Pure functions + small in-memory history per locomotive (for Δ/min). No I/O.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Literal

from app.schemas.simulator_frame import SimulatorFrame

UiSeverity = Literal["normal", "warning", "critical", "unknown"]

# Пороги в духе макета дашборда (норма → предупреждение → критично по отступу от диапазона)
@dataclass(frozen=True, slots=True)
class MetricBand:
    key: str
    label_ru: str
    unit: str
    norm_min: float | None
    norm_max: float | None
    warn_margin_ratio: float = 0.12  # доля ширины нормы для мягкой зоны


METRIC_BANDS: tuple[MetricBand, ...] = (
    MetricBand("speed", "Скорость", "km/h", 0.0, 140.0, 0.05),
    MetricBand("fuel_level", "Уровень топлива", "%", 10.0, 100.0, 0.08),
    MetricBand("brake_pressure", "Давление тормоза", "bar", 4.5, 6.5, 0.1),
    MetricBand("engine_temp", "Температура тяги", "°C", 0.0, 95.0, 0.06),
    MetricBand("voltage", "Напряжение", "V", 22.0, 28.0, 0.05),
    MetricBand("traction_current", "Ток нагрузки", "A", 0.0, 450.0, 0.07),
)

_HISTORY: dict[str, deque[tuple[float, dict[str, float]]]] = {}
_HISTORY_MAX = 32
_CODE_TO_UUID: dict[str, str] = {}


def remember_locomotive_uuid(code: str, uuid: str) -> None:
    """Заполняется после первого persist — следующие WS-кадры смогут отдать UUID."""
    _CODE_TO_UUID[code] = uuid


def _history_deque(loco_id: str) -> deque[tuple[float, dict[str, float]]]:
    d = _HISTORY.get(loco_id)
    if d is None:
        d = deque(maxlen=_HISTORY_MAX)
        _HISTORY[loco_id] = d
    return d


def _band_width(band: MetricBand) -> float:
    if band.norm_min is None or band.norm_max is None:
        return 0.0
    return max(band.norm_max - band.norm_min, 1e-6)


def severity_for_band(
    value: float | None,
    band: MetricBand,
) -> tuple[UiSeverity, float]:
    """
    Возвращает UI-статус и штраф 0..40 для индекса (0 = нет штрафа).
    """
    if value is None:
        return "unknown", 0.0
    lo, hi = band.norm_min, band.norm_max
    if lo is None or hi is None:
        return "normal", 0.0
    w = _band_width(band) * band.warn_margin_ratio
    if lo <= value <= hi:
        return "normal", 0.0
    if value < lo:
        gap = lo - value
        if gap > 2 * w:
            return "critical", min(40.0, 12.0 + gap * 8.0)
        return "warning", min(25.0, 6.0 + gap * 5.0)
    gap = value - hi
    if gap > 2 * w:
        return "critical", min(40.0, 12.0 + gap * 4.0)
    return "warning", min(25.0, 6.0 + gap * 3.0)


def _apply_simulator_hint(
    hint: str | None,
    index: float,
    status_order: int,
) -> tuple[float, int]:
    """Усиливаем критичность по health_hint симулятора. status_order: 0 norm, 1 att, 2 crit."""
    h = (hint or "ok").lower()
    if h == "critical":
        return min(index, 25.0), max(status_order, 2)
    if h in ("warning_high", "spike"):
        return min(index, 55.0), max(status_order, 1)
    if h in ("warning_low", "degrading", "glitch"):
        return min(index, 72.0), max(status_order, 1)
    return index, status_order


def _status_from_order(order: int) -> str:
    if order >= 2:
        return "critical"
    if order == 1:
        return "attention"
    return "normal"


def _trends_for_loco(loco_id: str, snapshot: dict[str, float]) -> dict[str, float | None]:
    dq = _history_deque(loco_id)
    now = time.monotonic()
    trends: dict[str, float | None] = {}
    if dq:
        prev_t, prev_m = dq[-1]
        dt_min = (now - prev_t) / 60.0
        if dt_min > 1e-6:
            for k, v in snapshot.items():
                if isinstance(v, (int, float)) and k in prev_m:
                    trends[f"{k}_per_min"] = (v - prev_m[k]) / dt_min
                else:
                    trends[f"{k}_per_min"] = None
        else:
            for k in snapshot:
                trends[f"{k}_per_min"] = None
    else:
        for k in snapshot:
            trends[f"{k}_per_min"] = None
    dq.append((now, dict(snapshot)))
    return trends


def _error_penalty(codes: list[str]) -> float:
    if not codes:
        return 0.0
    return min(35.0, 6.0 * len(codes) + 4.0)


def _top_factors(
    metric_penalties: list[tuple[str, str, float, UiSeverity]],
    error_codes: list[str],
    limit: int = 5,
) -> list[dict[str, Any]]:
    rows: list[tuple[float, dict[str, Any]]] = []
    for key, label, pen, sev in metric_penalties:
        if pen <= 0:
            continue
        impact = -round(min(40.0, pen), 1)
        rows.append(
            (
                pen,
                {
                    "key": key,
                    "label": label,
                    "impact_pct": impact,
                    "severity": sev,
                },
            )
        )
    for code in error_codes[:5]:
        rows.append(
            (
                15.0,
                {
                    "key": code,
                    "label": code.replace("_", " "),
                    "impact_pct": -8.0,
                    "severity": "warning",
                },
            )
        )
    rows.sort(key=lambda x: -x[0])
    return [r[1] for r in rows[:limit]]


def _alerts_from_metrics(
    frame: SimulatorFrame,
    metric_cards: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    bp = metric_cards.get("brake_pressure")
    if bp and bp["status"] in ("warning", "critical") and frame.oil_pressure is not None:
        out.append(
            {
                "severity": "critical" if bp["status"] == "critical" else "attention",
                "subsystem": "Тормозная система",
                "message": (
                    f"Давление тормоза вне нормы — сейчас {frame.oil_pressure} bar "
                    f"(норма {bp['norm_min']}–{bp['norm_max']} bar)."
                ),
            }
        )
    et = metric_cards.get("engine_temp")
    if et and et["status"] in ("warning", "critical") and frame.engine_temp is not None:
        out.append(
            {
                "severity": "attention",
                "subsystem": "Тяговый мотор",
                "message": (
                    f"Температура тяги повышена — {frame.engine_temp}°C, "
                    f"предел нормы {et['norm_max']}°C."
                ),
            }
        )
    v = metric_cards.get("voltage")
    if v and v["status"] in ("warning", "critical") and frame.voltage is not None:
        out.append(
            {
                "severity": "attention",
                "subsystem": "Электрическая система",
                "message": (
                    f"Напряжение вне нормы — {frame.voltage} V "
                    f"(норма {v['norm_min']}–{v['norm_max']} V)."
                ),
            }
        )
    c = metric_cards.get("traction_current")
    if c and c["status"] in ("warning", "critical") and frame.current is not None:
        out.append(
            {
                "severity": "attention",
                "subsystem": "Тяга",
                "message": (
                    f"Ток нагрузки выше нормы — {frame.current} A "
                    f"(макс. нормы {c['norm_max']} A)."
                ),
            }
        )
    return out[:6]


def _recommendations(metric_cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    et = metric_cards.get("engine_temp")
    if et and et["status"] != "normal":
        recs.append(
            {
                "priority": "high",
                "urgency_ru": "Немедленно",
                "action_ru": "Снизить нагрузку тяги на 15%",
                "reason_ru": "Снижение тепловыделения при приближении к пределу температуры.",
            }
        )
    bp = metric_cards.get("brake_pressure")
    if bp and bp["status"] != "normal":
        recs.append(
            {
                "priority": "high",
                "urgency_ru": "По графику остановки",
                "action_ru": "Проверить тормозную систему на ближайшей станции",
                "reason_ru": "Давление стабильно ниже нижней границы нормы.",
            }
        )
    if et and et["status"] == "warning":
        recs.append(
            {
                "priority": "medium",
                "urgency_ru": "Текущая операция",
                "action_ru": "Мониторить температуру 3 минуты",
                "reason_ru": "Если температура превысит 92°C до станции — протокол охлаждения.",
            }
        )
    v = metric_cards.get("voltage")
    if v and v["status"] == "warning":
        recs.append(
            {
                "priority": "low",
                "urgency_ru": "На следующем депо",
                "action_ru": "Зафиксировать событие напряжения для ТО",
                "reason_ru": "Нестабильное напряжение — возможен износ щёток генератора.",
            }
        )
    return recs[:6]


def build_live_payload(frame: SimulatorFrame) -> dict[str, Any]:
    """
    Собирает JSON для WebSocket: сырые поля, карточки метрик, индекс, алерты, рекомендации.
    """
    snapshot = {
        "speed": float(frame.speed) if frame.speed is not None else None,
        "fuel_level": float(frame.fuel_level) if frame.fuel_level is not None else None,
        "brake_pressure": float(frame.oil_pressure) if frame.oil_pressure is not None else None,
        "engine_temp": float(frame.engine_temp) if frame.engine_temp is not None else None,
        "voltage": float(frame.voltage) if frame.voltage is not None else None,
        "traction_current": float(frame.current) if frame.current is not None else None,
    }
    value_by_key = {k: v for k, v in snapshot.items() if v is not None}

    metric_cards: dict[str, dict[str, Any]] = {}
    penalties: list[tuple[str, str, float, UiSeverity]] = []
    status_order = 0

    for band in METRIC_BANDS:
        v = value_by_key.get(band.key)
        sev, pen = severity_for_band(v, band)
        if sev == "critical":
            status_order = max(status_order, 2)
        elif sev == "warning":
            status_order = max(status_order, 1)
        metric_cards[band.key] = {
            "value": v,
            "unit": band.unit,
            "label_ru": band.label_ru,
            "norm_min": band.norm_min,
            "norm_max": band.norm_max,
            "status": sev,
        }
        penalties.append((band.key, band.label_ru, pen, sev))

    metric_penalty_total = sum(p for _, _, p, _ in penalties)
    index = 100.0 - metric_penalty_total - _error_penalty(frame.error_codes)
    index = max(0.0, min(100.0, index))
    index, status_order = _apply_simulator_hint(frame.health_hint, index, status_order)
    health_status = _status_from_order(status_order)
    if index < 50 and health_status == "normal":
        health_status = "attention"
    if index < 25:
        health_status = "critical"

    trends = _trends_for_loco(
        frame.locomotive_id,
        {k: v for k, v in snapshot.items() if isinstance(v, (int, float))},
    )

    top_factors = _top_factors(penalties, frame.error_codes)
    alerts = _alerts_from_metrics(frame, metric_cards)
    recommendations = _recommendations(metric_cards)

    out: dict[str, Any] = {
        "timestamp": frame.timestamp,
        "locomotive_id": frame.locomotive_id,
        "mode": frame.mode,
        "health_hint": frame.health_hint,
        "error_codes": frame.error_codes,
        "health_index": round(index, 1),
        "health_status": health_status,
        "raw": {
            "speed": frame.speed,
            "fuel_level": frame.fuel_level,
            "engine_temp": frame.engine_temp,
            "oil_pressure": frame.oil_pressure,
            "voltage": frame.voltage,
            "current": frame.current,
        },
        "metrics": metric_cards,
        "trends": trends,
        "top_factors": top_factors,
        "alerts": alerts,
        "recommendations": recommendations,
    }
    uid = _CODE_TO_UUID.get(frame.locomotive_id)
    if uid:
        out["locomotive_uuid"] = uid
    return out
