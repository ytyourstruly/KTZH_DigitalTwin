"""
broadcaster.py — Manages connected WebSocket clients and broadcast loop.

Key responsibilities:
  - Register / unregister WebSocket connections
  - Run the async broadcast loop (calls engine.tick() every interval)
  - Apply jitter and optional random-disconnect fault injection
  - Support burst mode (temporarily increased message rate)
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from typing import Set

from fastapi import WebSocket
from engine import SimulationEngine
from telemetry import SimMode

logger = logging.getLogger("simulator.broadcaster")


class Broadcaster:
    def __init__(self, engine: SimulationEngine, config: dict) -> None:
        self.engine = engine
        self._cfg = config

        sim_cfg   = config.get("simulator", {})
        fault_cfg = config.get("fault_injection", {})

        self.interval_ms: int = sim_cfg.get("interval_ms", 300)
        self._burst_multiplier: int = sim_cfg.get("burst_multiplier", 10)
        self._auto_switch_sec: int = sim_cfg.get("auto_switch_interval_sec", 30)

        self.jitter_enabled: bool  = fault_cfg.get("jitter_enabled", True)
        self.jitter_max_ms: int    = fault_cfg.get("jitter_max_ms", 80)
        self.random_disconnects: bool       = fault_cfg.get("random_disconnects", False)
        self.disconnect_probability: float  = fault_cfg.get("disconnect_probability", 0.001)

        self.engine.missing_fields_enabled    = fault_cfg.get("missing_fields_enabled", False)
        self.engine.missing_field_probability = fault_cfg.get("missing_field_probability", 0.02)

        self._clients: Set[WebSocket] = set()
        self._burst_active: bool  = False
        self._messages_sent: int  = 0
        self._started_at: float   = time.monotonic()

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
        logger.info("Broadcast loop started (interval=%dms)", self.interval_ms)
        last_switch = time.monotonic()

        while True:
            # Auto mode switching
            if self._auto_switch_sec > 0:
                if time.monotonic() - last_switch >= self._auto_switch_sec:
                    self._advance_mode()
                    last_switch = time.monotonic()

            # Determine effective interval
            effective_ms = self.interval_ms
            if self._burst_active:
                effective_ms = max(50, self.interval_ms // self._burst_multiplier)

            # Jitter
            if self.jitter_enabled and self.jitter_max_ms > 0:
                jitter = random.uniform(0, self.jitter_max_ms / 1000.0)
            else:
                jitter = 0.0

            await asyncio.sleep(effective_ms / 1000.0 + jitter)

            if not self._clients:
                continue

            msg = self.engine.tick()
            payload = json.dumps(msg.model_dump())
            self._messages_sent += 1

            await self._broadcast(payload)

    async def _broadcast(self, payload: str) -> None:
        dead: list[WebSocket] = []

        for ws in list(self._clients):
            # Optional random disconnect fault
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
    # Control methods (called by REST endpoints)
    # ------------------------------------------------------------------

    def set_mode(self, mode: SimMode) -> None:
        self.engine.set_mode(mode)
        logger.info("Mode set to: %s", mode)

    def set_interval(self, ms: int) -> None:
        self.interval_ms = ms
        logger.info("Interval set to %dms", ms)

    def set_burst(self, active: bool) -> None:
        self._burst_active = active
        logger.info("Burst mode: %s", "ON" if active else "OFF")

    def reset(self) -> None:
        self.engine.reset()
        self.engine.set_mode(SimMode.NORMAL)
        self._burst_active = False
        logger.info("Simulator reset to NORMAL")

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def status(self) -> dict:
        return {
            "mode":              self.engine.mode.value,
            "interval_ms":       self.interval_ms,
            "burst_active":      self._burst_active,
            "connected_clients": len(self._clients),
            "messages_sent":     self._messages_sent,
            "uptime_seconds":    round(time.monotonic() - self._started_at, 1),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _advance_mode(self) -> None:
        self._mode_index = (self._mode_index + 1) % len(self._mode_sequence)
        new_mode = self._mode_sequence[self._mode_index]
        self.engine.set_mode(new_mode)
        logger.info("Auto-switched mode → %s", new_mode)