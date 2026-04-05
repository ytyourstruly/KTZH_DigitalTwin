"""
Rule-based live dashboard view from a simulator frame: thresholds, health index, trends, factors.

Штрафы и рекомендации считаются от норм полосы (gap / w)
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

from app.schemas.simulator_frame import SimulatorFrame

UiSeverity = Literal["normal", "warning", "critical", "unknown"]


@dataclass(frozen=True, slots=True)
class MetricBand:
    key: str
    label_ru: str
    unit: str
    norm_min: float | None
    norm_max: float | None
    warn_margin_ratio: float


METRIC_BANDS: tuple[MetricBand, ...] = (
    MetricBand("speed", "Скорость", "km/h", 0.0, 140.0, 0.05),
    MetricBand("fuel_level", "Уровень топлива", "%", 10.0, 100.0, 0.08),
    MetricBand("brake_pressure", "Давление тормоза", "bar", 4.5, 6.5, 0.1),
    MetricBand("engine_temp", "Температура тяги", "°C", 0.0, 95.0, 0.06),
    MetricBand("voltage", "Напряжение", "V", 22.0, 28.0, 0.05),
    MetricBand("traction_current", "Ток нагрузки", "A", 0.0, 450.0, 0.07),
)

_HISTORY: dict[str, deque[tuple[float, dict[str, float]]]] = {}
_CODE_TO_UUID: dict[str, str] = {}


def remember_locomotive_uuid(code: str, uuid: str) -> None:
    """Заполняется после первого persist — следующие WS-кадры смогут отдать UUID."""
    _CODE_TO_UUID[code] = uuid


def _history_deque(loco_id: str) -> deque[tuple[float, dict[str, float]]]:
    maxlen = max(8, min(64, len(METRIC_BANDS) * 8))
    d = _HISTORY.get(loco_id)
    if d is None or d.maxlen != maxlen:
        d = deque(maxlen=maxlen)
        _HISTORY[loco_id] = d
    return d


def _band_width(band: MetricBand) -> float:
    if band.norm_min is None or band.norm_max is None:
        return 0.0
    return max(band.norm_max - band.norm_min, 1e-6)


def _soft_margin(band: MetricBand) -> float:
    return _band_width(band) * band.warn_margin_ratio


def _penalty_and_severity(gap: float, w: float) -> tuple[UiSeverity, float]:
    """Штраф только из gap и ширины мягкой зоны w: penalty = gap²/w, severity по gap/w."""
    if gap <= 0:
        return "normal", 0.0
    den = max(w, 1e-9)
    ratio = gap / den
    severity: UiSeverity = "critical" if ratio > 2.0 else "warning"
    penalty = min(100.0, (gap * gap) / den)
    return severity, penalty


def severity_for_band(
    value: float | None,
    band: MetricBand,
) -> tuple[UiSeverity, float]:
    if value is None:
        return "unknown", 0.0
    lo, hi = band.norm_min, band.norm_max
    if lo is None or hi is None:
        return "normal", 0.0
    w = _soft_margin(band)
    if lo <= value <= hi:
        return "normal", 0.0
    if value < lo:
        return _penalty_and_severity(lo - value, w)
    return _penalty_and_severity(value - hi, w)


@lru_cache(maxsize=1)
def _theoretical_max_metric_penalty() -> float:
    """Сумма штрафов, если по каждой метрике отклонение ≈ 2.5× полной ширины нормы."""
    total = 0.0
    for band in METRIC_BANDS:
        bw = _band_width(band)
        w = _soft_margin(band)
        gap = 2.5 * bw
        _, p = _penalty_and_severity(gap, w)
        total += p
    return max(total, 1e-6)


def _apply_simulator_hint(
    hint: str | None,
    index: float,
    status_order: int,
    metric_penalty_total: float,
) -> tuple[float, int]:
    """Корректируем индекс по health_hint; сила — только stress = доля от теор. max штрафов."""
    h = (hint or "ok").lower()
    tmax = _theoretical_max_metric_penalty()
    stress = min(1.0, metric_penalty_total / tmax)
    damp = stress ** 0.5
    rel_idx = index / 100.0
    if h == "critical":
        # Только снижение индекса, factor ∈ (0, 1]
        factor = max(0.05, min(1.0, 1.0 - damp))
        return index * factor, max(status_order, 2)
    if h in ("warning_high", "spike"):
        factor = min(
            1.0,
            max(rel_idx * 0.5, 1.0 - damp * (1.0 - rel_idx * 0.28)),
        )
        return index * factor, max(status_order, 1)
    if h in ("warning_low", "degrading", "glitch"):
        factor = min(
            1.0,
            max(0.35 + rel_idx * 0.45, 1.0 - damp * (1.0 - rel_idx * 0.52)),
        )
        return index * factor, max(status_order, 1)
    return index, status_order


def _resolve_health_status(index: float, status_order: int) -> str:
    """
    Сначала интегральный индекс даёт базовую оценку (норма / внимание / критично).

    Если **хотя бы одна метрика** в UI-состоянии ``critical`` (выход за порог ratio > 2),
    общий ``health_status`` всегда ``critical``: один критичный узел для машиниста важнее
    того, что усреднённый индекс ещё может оставаться высоким из‑за остальных «зелёных» полей.
    Предупреждения без critical лишь не дают оставаться «норма» — поднимают до ``attention``.
    """
    if status_order >= 2:
        return "critical"

    if index >= 80.0:
        overall = "normal"
    elif index >= 50.0:
        overall = "attention"
    else:
        overall = "critical"

    if status_order >= 1 and overall == "normal":
        return "attention"
    return overall


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


def _error_penalty(codes: list[str], metric_penalty_total: float) -> float:
    if not codes:
        return 0.0
    per_band_avg = metric_penalty_total / len(METRIC_BANDS)
    # Вклад кода растёт со средним стрессом по метрикам
    raw = len(codes) * (per_band_avg + _theoretical_max_metric_penalty() / (len(METRIC_BANDS) + len(codes)))
    headroom = max(0.0, 100.0 - metric_penalty_total)
    return min(headroom, raw)


def _top_factors(
    metric_penalties: list[tuple[str, str, float, UiSeverity]],
    error_codes: list[str],
    metric_penalty_total: float,
    limit: int,
) -> list[dict[str, Any]]:
    tmax = _theoretical_max_metric_penalty()
    scale = 100.0 / tmax
    worst_pen = max((p for _, _, p, _ in metric_penalties), default=0.0)
    worst_scaled = worst_pen * scale
    rows: list[tuple[float, dict[str, Any]]] = []
    for key, label, pen, sev in metric_penalties:
        if pen <= 0:
            continue
        imp_mag = pen * scale
        # «Критично» по узкому диапазону даёт малый gap²/w, но для UI вклад не ниже доли от худшего штрафа
        if sev == "critical":
            imp_mag = max(imp_mag, worst_scaled * (pen / max(worst_pen, 1e-9)) ** 0.35)
            imp_mag = max(imp_mag, worst_scaled * 0.82)
        impact = -round(min(40.0, imp_mag), 1)
        rows.append((pen, {"key": key, "label": label, "impact_pct": max(-40.0, impact), "severity": sev}))
    n_err = len(error_codes)
    for i, code in enumerate(error_codes):
        share = metric_penalty_total / max(n_err, 1)
        pen_equiv = share * (1.0 + i / max(n_err, 1))
        impact = -round(min(35.0, pen_equiv * scale), 1)
        rows.append(
            (
                pen_equiv,
                {"key": code, "label": code.replace("_", " "), "impact_pct": max(-35.0, impact), "severity": "warning"},
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
        lo = float(bp["norm_min"])
        p = float(frame.oil_pressure)
        deficit = max(0.0, (lo - p) / max(lo, 1e-9))
        out.append(
            {
                "severity": "critical" if bp["status"] == "critical" else "attention",
                "subsystem": "Тормозная система",
                "message": (
                    f"Давление тормоза вне нормы — {p} bar (норма {bp['norm_min']}–{bp['norm_max']} bar), "
                    f"ниже нижнего порога на {deficit * 100:.1f}% от величины порога."
                ),
            }
        )
    et = metric_cards.get("engine_temp")
    if et and et["status"] in ("warning", "critical") and frame.engine_temp is not None:
        hi = float(et["norm_max"])
        v = float(frame.engine_temp)
        over = max(0.0, v - hi)
        span = max(float(et["norm_max"]) - float(et["norm_min"] or 0), 1e-6)
        out.append(
            {
                "severity": "attention",
                "subsystem": "Тяговый мотор",
                "message": (
                    f"Температура тяги {v}°C (норма до {hi}°C); превышение {over:.1f}°C "
                    f"({over / span * 100:.1f}% от ширины нормального диапазона)."
                ),
            }
        )
    vcard = metric_cards.get("voltage")
    if vcard and vcard["status"] in ("warning", "critical") and frame.voltage is not None:
        lo, hi = float(vcard["norm_min"]), float(vcard["norm_max"])
        mid = (lo + hi) / 2.0
        fv = float(frame.voltage)
        dev = abs(fv - mid) / max(hi - lo, 1e-6)
        out.append(
            {
                "severity": "attention",
                "subsystem": "Электрическая система",
                "message": (
                    f"Напряжение {fv} V (норма {lo}–{hi} V); отклонение от середины диапазона "
                    f"{dev * 100:.1f}% от его ширины."
                ),
            }
        )
    c = metric_cards.get("traction_current")
    if c and c["status"] in ("warning", "critical") and frame.current is not None:
        hi = float(c["norm_max"])
        cur = float(frame.current)
        over = max(0.0, cur - hi)
        out.append(
            {
                "severity": "attention",
                "subsystem": "Тяга",
                "message": (
                    f"Ток нагрузки {cur} A при максимуме нормы {hi} A; запас до предела "
                    f"{over:.1f} A."
                ),
            }
        )
    return out[: len(METRIC_BANDS)]


def _traction_reduction_pct(et: dict[str, Any]) -> int:
    """Доля нагрузки: доля пути от mid до hi, усиленная при critical (через штрафную полосу w)."""
    v = et.get("value")
    lo = et.get("norm_min")
    hi = et.get("norm_max")
    if v is None or lo is None or hi is None:
        return 0
    lo, hi, v = float(lo), float(hi), float(v)
    band = next(b for b in METRIC_BANDS if b.key == "engine_temp")
    w = _soft_margin(band)
    mid = (lo + hi) / 2.0
    span_hi = max(hi - mid, 1e-9)
    if v <= mid:
        base = 0.0
    else:
        base = (v - mid) / span_hi
    base = max(0.0, min(1.0, base))
    status = et.get("status")
    if status == "critical":
        urgency = min(1.0, base + w / max(hi - lo, 1e-9))
    elif status == "warning":
        urgency = base * (1.0 - w / max(2 * (hi - lo), 1e-9))
    else:
        urgency = 0.0
    pct = int(round(base * 100 * max(urgency, 0.15)))
    return max(5, min(50, pct))


def _monitor_minutes_engine_temp(et: dict[str, Any], trends: dict[str, float | None]) -> int:
    v = et.get("value")
    hi = et.get("norm_max")
    lo = et.get("norm_min")
    if v is None or hi is None:
        return 1
    v, hi = float(v), float(hi)
    lo = float(lo or 0.0)
    headroom = max(0.0, hi - v)
    span = max(hi - lo, 1e-6)
    tr = trends.get("engine_temp_per_min")
    if tr is not None and tr > 1e-9:
        est_min = headroom / tr
        cap = int(round(span / tr)) if tr > 1e-9 else int(round(headroom))
        return max(1, min(max(cap, 1), int(round(est_min))))
    if tr is not None and tr < -1e-9:
        return max(1, int(round(headroom * len(METRIC_BANDS) / max(span, 1e-6))))
    return max(1, int(round(headroom * len(METRIC_BANDS) / max(span, 1e-6))))


def _temp_trip_celsius(et: dict[str, Any]) -> float:
    hi = float(et.get("norm_max") or 95.0)
    band = next(b for b in METRIC_BANDS if b.key == "engine_temp")
    w = _soft_margin(band)
    # Контрольная отметка: верх нормы минус мягкая зона (эквивалентно hi - min(w, …))
    return hi - w


def _recommendations(
    metric_cards: dict[str, dict[str, Any]],
    trends: dict[str, float | None],
    frame: SimulatorFrame,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    et = metric_cards.get("engine_temp")
    if et and et["status"] != "normal":
        pct = _traction_reduction_pct(et)
        recs.append(
            {
                "priority": "high",
                "urgency_ru": "Немедленно",
                "action_ru": f"Снизить нагрузку тяги примерно на {pct}%",
                "reason_ru": (
                    f"Оценка по T={et.get('value')}°C и полосе нормы "
                    f"[{et.get('norm_min')}–{et.get('norm_max')}]: снижение нагрузки уменьшит тепловыделение."
                ),
            }
        )
    bp = metric_cards.get("brake_pressure")
    if bp and bp["status"] != "normal" and frame.oil_pressure is not None:
        lo = float(bp["norm_min"])
        p = float(frame.oil_pressure)
        deficit = max(0.0, (lo - p) / max(lo, 1e-9))
        recs.append(
            {
                "priority": "high",
                "urgency_ru": "По графику остановки",
                "action_ru": "Проверить тормозную систему на ближайшей станции",
                "reason_ru": (
                    f"Текущее давление {p} bar ниже нижней границы {lo} bar "
                    f"на {deficit * 100:.1f}% от величины нижнего порога."
                ),
            }
        )
    if et and et["status"] == "warning":
        v_m = et.get("value")
        hi_m = et.get("norm_max")
        if (
            v_m is not None
            and hi_m is not None
            and float(v_m) > float(hi_m)
        ):
            over = float(v_m) - float(hi_m)
            recs.append(
                {
                    "priority": "medium",
                    "urgency_ru": "Немедленно",
                    "action_ru": "Ограничить тягу до выхода температуры в норму",
                    "reason_ru": (
                        f"T={v_m}°C уже выше верхней границы {hi_m}°C на {over:.1f}°C — "
                        f"удерживать наблюдение до отката; при дальнейшем росте — протокол охлаждения."
                    ),
                }
            )
        else:
            mins = _monitor_minutes_engine_temp(et, trends)
            trip = _temp_trip_celsius(et)
            recs.append(
                {
                    "priority": "medium",
                    "urgency_ru": "Текущая операция",
                    "action_ru": f"Мониторить температуру около {mins} мин",
                    "reason_ru": (
                        f"При сохранении тренда контролировать доход до ~{trip:.1f}°C "
                        f"(ниже верхней границы {et.get('norm_max')}°C); дальше — протокол охлаждения."
                    ),
                }
            )
    vcard = metric_cards.get("voltage")
    if vcard and vcard["status"] == "warning" and frame.voltage is not None:
        lo, hi = float(vcard["norm_min"]), float(vcard["norm_max"])
        mid = (lo + hi) / 2.0
        dev_v = abs(float(frame.voltage) - mid)
        recs.append(
            {
                "priority": "low",
                "urgency_ru": "На следующем депо",
                "action_ru": "Зафиксировать событие напряжения для ТО",
                "reason_ru": (
                    f"Напряжение отклоняется от середины нормы ({mid:.1f} V) на {dev_v:.2f} V "
                    f"при полосе {lo}–{hi} V — целесообразна запись для обслуживания."
                ),
            }
        )
    return recs[: len(METRIC_BANDS) + 2]


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
    err_pen = _error_penalty(frame.error_codes, metric_penalty_total)
    index = 100.0 - metric_penalty_total - err_pen
    index = max(0.0, min(100.0, index))
    index, status_order = _apply_simulator_hint(
        frame.health_hint, index, status_order, metric_penalty_total
    )
    index = max(0.0, min(100.0, index))
    health_status = _resolve_health_status(index, status_order)

    trends = _trends_for_loco(
        frame.locomotive_id,
        {k: v for k, v in snapshot.items() if isinstance(v, (int, float))},
    )

    top_factors = _top_factors(
        penalties, frame.error_codes, metric_penalty_total, limit=len(METRIC_BANDS)
    )
    alerts = _alerts_from_metrics(frame, metric_cards)
    recommendations = _recommendations(metric_cards, trends, frame)

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
