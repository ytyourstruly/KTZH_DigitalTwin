"""
broadcaster.py — Manages connected WebSocket clients and broadcast loop.

Key responsibilities:
  - Register / unregister WebSocket connections
  - Run the async broadcast loop (calls engine.tick() every interval)
  - Apply jitter and optional random-disconnect fault injection
  - Hz-based frequency presets with auto-expiring burst mode
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from typing import Optional, Set

from fastapi import WebSocket
from engine import SimulationEngine
from telemetry import (
    SimMode, FrequencyPreset, PRESET_HZ, BURST_DURATION_SEC,
)

logger = logging.getLogger("simulator.broadcaster")


# ---------------------------------------------------------------------------
# Hz ↔ ms helpers
# ---------------------------------------------------------------------------

def _hz_to_ms(hz: float) -> int:
    """Convert frequency in Hz to interval in whole milliseconds."""
    return max(1, round(1000.0 / hz))

def _ms_to_hz(ms: int) -> float:
    """Convert interval in ms to Hz, rounded to 2 dp."""
    return round(1000.0 / ms, 2)


class Broadcaster:
    def __init__(self, engine: SimulationEngine, config: dict) -> None:
        self.engine = engine
        self._cfg = config

        sim_cfg   = config.get("simulator", {})
        fault_cfg = config.get("fault_injection", {})

        self._auto_switch_sec: int = sim_cfg.get("auto_switch_interval_sec", 30)

        self.jitter_enabled: bool  = fault_cfg.get("jitter_enabled", True)
        self.jitter_max_ms: int    = fault_cfg.get("jitter_max_ms", 80)
        self.random_disconnects: bool       = fault_cfg.get("random_disconnects", False)
        self.disconnect_probability: float  = fault_cfg.get("disconnect_probability", 0.001)

        self.engine.missing_fields_enabled    = fault_cfg.get("missing_fields_enabled", False)
        self.engine.missing_field_probability = fault_cfg.get("missing_field_probability", 0.02)

        self._clients: Set[WebSocket] = set()
        self._messages_sent: int  = 0
        self._started_at: float   = time.monotonic()

        # ------------------------------------------------------------------
        # Frequency state
        # ------------------------------------------------------------------
        # The "base" preset is what we return to after burst expires.
        self._base_preset: FrequencyPreset  = FrequencyPreset.NORMAL
        self._active_preset: FrequencyPreset = FrequencyPreset.NORMAL
        # interval_ms is always derived from the active preset (or set directly
        # via /rate for backwards-compat raw ms control).
        self.interval_ms: int = _hz_to_ms(PRESET_HZ[FrequencyPreset.NORMAL])

        # When burst is active this is the monotonic timestamp of expiry.
        self._burst_expires_at: Optional[float] = None

        # Mode auto-switch sequence
        self._mode_sequence = [
            SimMode.NORMAL,
            SimMode.DEGRADATION,
            SimMode.SPIKE,
            SimMode.FAILURE,
            SimMode.NORMAL,
        ]
        self._mode_index = 0

    # ------------------------------------------------------------------
    # Client management
    # ------------------------------------------------------------------

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)
        logger.info("Client connected: %s — total=%d", ws.client, len(self._clients))

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)
        logger.info("Client disconnected: %s — total=%d", ws.client, len(self._clients))

    # ------------------------------------------------------------------
    # Broadcast loop
    # ------------------------------------------------------------------

    async def run_broadcast_loop(self) -> None:
        """Main loop: ticks the engine and broadcasts to all clients."""
        logger.info(
            "Broadcast loop started — preset=%s  interval=%dms  (%.1f Hz)",
            self._active_preset, self.interval_ms, _ms_to_hz(self.interval_ms),
        )
        last_switch = time.monotonic()

        while True:
            now = time.monotonic()

            # ----------------------------------------------------------
            # Auto mode switching
            # ----------------------------------------------------------
            if self._auto_switch_sec > 0:
                if now - last_switch >= self._auto_switch_sec:
                    self._advance_mode()
                    last_switch = now

            # ----------------------------------------------------------
            # Burst expiry check  — revert to base preset automatically
            # ----------------------------------------------------------
            if (
                self._burst_expires_at is not None
                and now >= self._burst_expires_at
            ):
                self._burst_expires_at = None
                self._active_preset = self._base_preset
                self.interval_ms = _hz_to_ms(PRESET_HZ[self._base_preset])
                logger.info(
                    "Burst expired → reverted to preset=%s  interval=%dms  (%.1f Hz)",
                    self._active_preset, self.interval_ms,
                    _ms_to_hz(self.interval_ms),
                )

            # ----------------------------------------------------------
            # Jitter
            # ----------------------------------------------------------
            if self.jitter_enabled and self.jitter_max_ms > 0:
                jitter = random.uniform(0, self.jitter_max_ms / 1000.0)
            else:
                jitter = 0.0

            await asyncio.sleep(self.interval_ms / 1000.0 + jitter)

            if not self._clients:
                continue

            msg = self.engine.tick()
            payload = json.dumps(msg.model_dump())
            self._messages_sent += 1

            await self._broadcast(payload)

    async def _broadcast(self, payload: str) -> None:
        dead: list[WebSocket] = []

        for ws in list(self._clients):
            if self.random_disconnects:
                if random.random() < self.disconnect_probability:
                    logger.warning("Fault injection: forcing disconnect on %s", ws.client)
                    try:
                        await ws.close(code=1001)
                    except Exception:
                        pass
                    dead.append(ws)
                    continue
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.debug("Send failed (%s): %s", ws.client, exc)
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

    # ------------------------------------------------------------------
    # Frequency control  (primary API)
    # ------------------------------------------------------------------

    def set_frequency(self, preset: FrequencyPreset) -> dict:
        """
        Apply a named frequency preset.

        - NORMAL / HIGHLOAD — persistent; stored as the base preset.
        - BURST             — 50 Hz for BURST_DURATION_SEC seconds, then
                              automatically reverts to the current base preset.
        Returns a dict suitable for the API response.
        """
        hz = PRESET_HZ[preset]
        ms = _hz_to_ms(hz)

        if preset == FrequencyPreset.BURST:
            # Don't overwrite the base preset — we need it for revert
            self._active_preset    = FrequencyPreset.BURST
            self.interval_ms       = ms
            self._burst_expires_at = time.monotonic() + BURST_DURATION_SEC
            logger.info(
                "Frequency → BURST  50 Hz / %dms  (reverts in %ds)",
                ms, BURST_DURATION_SEC,
            )
            return {
                "preset":         preset,
                "frequency_hz":   hz,
                "interval_ms":    ms,
                "burst_duration_sec": BURST_DURATION_SEC,
                "reverts_to":     self._base_preset,
            }

        # NORMAL or HIGHLOAD — persistent
        self._base_preset    = preset
        self._active_preset  = preset
        self.interval_ms     = ms
        self._burst_expires_at = None          # cancel any running burst
        logger.info("Frequency → %s  %.1f Hz / %dms", preset.upper(), hz, ms)
        return {
            "preset":       preset,
            "frequency_hz": hz,
            "interval_ms":  ms,
        }

    # ------------------------------------------------------------------
    # Legacy / raw interval control (backwards-compat with /rate)
    # ------------------------------------------------------------------

    def set_interval(self, ms: int) -> None:
        """Set interval directly in ms (raw control, no preset label)."""
        self.interval_ms     = ms
        self._active_preset  = FrequencyPreset.NORMAL   # best-effort label
        self._base_preset    = FrequencyPreset.NORMAL
        self._burst_expires_at = None
        logger.info("Interval set directly to %dms (%.1f Hz)", ms, _ms_to_hz(ms))

    # ------------------------------------------------------------------
    # Other control methods
    # ------------------------------------------------------------------

    def set_mode(self, mode: SimMode) -> None:
        self.engine.set_mode(mode)
        logger.info("Mode set to: %s", mode)

    def set_burst(self, active: bool) -> None:
        """Legacy burst toggle — delegates to the new frequency system."""
        if active:
            self.set_frequency(FrequencyPreset.BURST)
        else:
            self.set_frequency(self._base_preset)

    def reset(self) -> None:
        self.engine.reset()
        self.engine.set_mode(SimMode.NORMAL)
        self.set_frequency(FrequencyPreset.NORMAL)
        logger.info("Simulator reset to NORMAL")

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def burst_active(self) -> bool:
        return self._burst_expires_at is not None

    @property
    def burst_expires_in_sec(self) -> Optional[float]:
        if self._burst_expires_at is None:
            return None
        remaining = self._burst_expires_at - time.monotonic()
        return round(max(0.0, remaining), 2)

    @property
    def status(self) -> dict:
        return {
            "mode":                  self.engine.mode.value,
            "interval_ms":           self.interval_ms,
            "frequency_hz":          _ms_to_hz(self.interval_ms),
            "frequency_preset":      self._active_preset.value,
            "burst_active":          self.burst_active,
            "burst_expires_in_sec":  self.burst_expires_in_sec,
            "connected_clients":     len(self._clients),
            "messages_sent":         self._messages_sent,
            "uptime_seconds":        round(time.monotonic() - self._started_at, 1),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _advance_mode(self) -> None:
        self._mode_index = (self._mode_index + 1) % len(self._mode_sequence)
        new_mode = self._mode_sequence[self._mode_index]
        self.engine.set_mode(new_mode)
        logger.info("Auto-switched mode → %s", new_mode)