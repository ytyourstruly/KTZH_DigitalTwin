"""
engine.py — Stateful simulation engine.

Maintains current parameter values and advances them each tick
according to the active SimMode.
"""

from __future__ import annotations

import math
import random
import time
from datetime import datetime, timezone
from typing import Optional

from telemetry import (
    RANGES, ALL_ERROR_CODES, SimMode, TelemetryMessage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def _gauss(centre: float, sigma: float) -> float:
    return random.gauss(centre, sigma)

def _round2(v: float) -> float:
    return round(v, 2)


# ---------------------------------------------------------------------------
# SimulationEngine
# ---------------------------------------------------------------------------

class SimulationEngine:
    """
    Owns the current locomotive state and produces TelemetryMessage objects.

    Modes:
      NORMAL      — parameters wander slightly around realistic centres
      DEGRADATION — parameters drift toward warning boundaries over time
      SPIKE       — random sudden jumps then recovery
      FAILURE     — parameters at/past critical thresholds + error codes
    """

    def __init__(self, locomotive_id: str) -> None:
        self.locomotive_id = locomotive_id
        self.mode: SimMode = SimMode.NORMAL

        # Internal continuous state (floats, updated each tick)
        self._state: dict[str, float] = {
            k: v["centre"] for k, v in RANGES.items()
        }

        # Degradation accumulator (0.0 → 1.0 = fully degraded)
        self._degradation: float = 0.0

        # Spike state
        self._spike_active: bool = False
        self._spike_field: Optional[str] = None
        self._spike_ticks_left: int = 0

        # Fault injection toggles (set externally)
        self.missing_fields_enabled: bool = False
        self.missing_field_probability: float = 0.02

        self._mode_entered_at: float = time.monotonic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_mode(self, mode: SimMode) -> None:
        self.mode = mode
        self._mode_entered_at = time.monotonic()
        if mode == SimMode.NORMAL:
            self.reset()

    def reset(self) -> None:
        """Snap state back to nominal values."""
        for k, v in RANGES.items():
            self._state[k] = v["centre"]
        self._degradation = 0.0
        self._spike_active = False

    def tick(self) -> TelemetryMessage:
        """Advance simulation one step and return a telemetry message."""
        if self.mode == SimMode.NORMAL:
            self._tick_normal()
        elif self.mode == SimMode.DEGRADATION:
            self._tick_degradation()
        elif self.mode == SimMode.SPIKE:
            self._tick_spike()
        elif self.mode == SimMode.FAILURE:
            self._tick_failure()

        return self._build_message()

    # ------------------------------------------------------------------
    # Private tick logic
    # ------------------------------------------------------------------

    def _tick_normal(self) -> None:
        """Stable, slightly noisy wandering around centre values."""
        for key, r in RANGES.items():
            drift = _gauss(0, r["sigma"] * 0.3)
            # Gentle mean-reversion pull
            pull  = (r["centre"] - self._state[key]) * 0.05
            self._state[key] = _clamp(
                self._state[key] + drift + pull,
                r["min"], r["max"]
            )
        # Fuel drains very slowly
        self._state["fuel_level"] -= random.uniform(0.0005, 0.001)
        self._state["fuel_level"] = max(0, self._state["fuel_level"])

    def _tick_degradation(self) -> None:
        """Parameters drift toward failure boundaries at increasing rate."""
        elapsed = time.monotonic() - self._mode_entered_at
        # Degradation grows with sqrt(t), max ~0.95 at 5 minutes
        self._degradation = min(0.95, math.sqrt(elapsed / 300.0))

        d = self._degradation

        # Temperature creeps up
        self._state["engine_temp"] = _clamp(
            _gauss(88 + d * 35, 1.5),
            RANGES["engine_temp"]["min"], RANGES["engine_temp"]["max"]
        )
        # Oil pressure drops
        self._state["oil_pressure"] = _clamp(
            _gauss(3.8 - d * 2.0, 0.15),
            RANGES["oil_pressure"]["min"], RANGES["oil_pressure"]["max"]
        )
        # Voltage sags
        self._state["voltage"] = _clamp(
            _gauss(27.5 - d * 4.0, 0.3),
            RANGES["voltage"]["min"], RANGES["voltage"]["max"]
        )
        # Speed becomes erratic
        self._state["speed"] = _clamp(
            _gauss(85 - d * 30, 8),
            0, RANGES["speed"]["max"]
        )
        # Current spikes as systems struggle
        self._state["current"] = _clamp(
            _gauss(420 + d * 300, 20),
            RANGES["current"]["min"], RANGES["current"]["max"]
        )
        # Fuel drains faster under stress
        self._state["fuel_level"] -= random.uniform(0.002, 0.005)
        self._state["fuel_level"] = max(0, self._state["fuel_level"])

    def _tick_spike(self) -> None:
        """
        Mostly normal, but every ~15 ticks one field spikes hard
        then recovers over 3-5 ticks.
        """
        # First bring everything back toward normal
        self._tick_normal()

        if self._spike_active:
            field = self._spike_field
            r = RANGES[field]
            # Hold spike value with small noise
            spike_target = r["max"] * 0.97
            self._state[field] = _clamp(
                _gauss(spike_target, r["sigma"]),
                r["min"], r["max"]
            )
            self._spike_ticks_left -= 1
            if self._spike_ticks_left <= 0:
                self._spike_active = False
        else:
            if random.random() < 0.07:   # ~7% chance per tick to start a spike
                self._spike_field = random.choice(list(RANGES.keys()))
                self._spike_ticks_left = random.randint(3, 7)
                self._spike_active = True

    def _tick_failure(self) -> None:
        """Push multiple parameters into critical territory."""
        self._state["engine_temp"] = _clamp(
            _gauss(118, 1.5), 0, RANGES["engine_temp"]["max"]
        )
        self._state["oil_pressure"] = _clamp(
            _gauss(1.6, 0.1), 0, RANGES["oil_pressure"]["max"]
        )
        self._state["voltage"] = _clamp(
            _gauss(22.5, 0.5), 0, RANGES["voltage"]["max"]
        )
        self._state["current"] = _clamp(
            _gauss(780, 25), 0, RANGES["current"]["max"]
        )
        self._state["speed"] = _clamp(
            _gauss(15, 5), 0, RANGES["speed"]["max"]
        )
        self._state["fuel_level"] -= random.uniform(0.01, 0.03)
        self._state["fuel_level"] = max(0, self._state["fuel_level"])

    # ------------------------------------------------------------------
    # Message builder
    # ------------------------------------------------------------------

    def _build_message(self) -> TelemetryMessage:
        ts = datetime.now(timezone.utc).isoformat()

        # Determine error codes
        errors = self._compute_errors()

        # Determine health hint
        hint = self._health_hint(errors)

        fields = dict(
            timestamp     = ts,
            locomotive_id = self.locomotive_id,
            speed         = _round2(self._state["speed"]),
            fuel_level    = _round2(self._state["fuel_level"]),
            engine_temp   = _round2(self._state["engine_temp"]),
            oil_pressure  = _round2(self._state["oil_pressure"]),
            voltage       = _round2(self._state["voltage"]),
            current       = _round2(self._state["current"]),
            error_codes   = errors,
            health_hint   = hint,
            mode          = self.mode.value,
        )

        # Optional: randomly drop fields to stress-test backend validation
        if self.missing_fields_enabled:
            droppable = [
                "speed", "fuel_level", "engine_temp",
                "oil_pressure", "voltage", "current",
            ]
            for f in droppable:
                if random.random() < self.missing_field_probability:
                    fields[f] = None

        return TelemetryMessage(**fields)

    def _compute_errors(self) -> list[str]:
        codes: list[str] = []

        if self.mode == SimMode.FAILURE:
            # Always emit several critical codes in failure mode
            codes = random.sample(ALL_ERROR_CODES, k=random.randint(3, 6))
            return codes

        if self.mode == SimMode.DEGRADATION:
            d = self._degradation
            if self._state["engine_temp"] > 105:
                codes.append("E001_OVERHEAT")
            if self._state["oil_pressure"] < 2.2:
                codes.append("E002_LOW_OIL")
            if self._state["fuel_level"] < 20:
                codes.append("E003_LOW_FUEL")
            if self._state["voltage"] < 24.0:
                codes.append("E004_VOLTAGE_DROP")
            if self._state["current"] > 700:
                codes.append("E005_OVERCURRENT")
            if d > 0.7 and random.random() < 0.3:
                codes.append("E006_SENSOR_FAULT")
            return codes

        if self.mode == SimMode.SPIKE:
            # Occasional spurious code during spike
            if self._spike_active and random.random() < 0.4:
                codes.append(random.choice(ALL_ERROR_CODES[:5]))
            return codes

        # NORMAL — very rare random glitch
        if random.random() < 0.005:
            codes.append("E006_SENSOR_FAULT")
        return codes

    def _health_hint(self, errors: list[str]) -> str:
        if self.mode == SimMode.FAILURE:
            return "critical"
        if self.mode == SimMode.DEGRADATION:
            if self._degradation > 0.7:
                return "warning_high"
            if self._degradation > 0.3:
                return "warning_low"
            return "degrading"
        if self.mode == SimMode.SPIKE:
            return "spike" if self._spike_active else "ok"
        if errors:
            return "glitch"
        return "ok"