"""Background task: consume simulator WebSocket, persist, fan-out to dashboard clients."""

from __future__ import annotations

import asyncio
import json
import time

import websockets

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.db.session import async_session
from app.provider.service_provider import ServiceProvider
from app.realtime.telemetry_hub import broadcast_telemetry
from app.schemas.simulator_frame import SimulatorFrame
from app.services.loco.simulator_sync import apply_simulator_frame

logger = get_logger("realtime.simulator_client")

_last_snapshot_mono: dict[str, float] = {}


def _should_snapshot(loco_code: str, interval_sec: float) -> bool:
    now = time.monotonic()
    prev = _last_snapshot_mono.get(loco_code, 0.0)
    if now - prev >= interval_sec:
        _last_snapshot_mono[loco_code] = now
        return True
    return False


async def run_simulator_ingest_loop() -> None:
    settings = get_settings()
    url = settings.simulator_ws_url
    delay = settings.simulator_reconnect_delay_sec
    snap_iv = settings.telemetry_snapshot_interval_sec

    while True:
        try:
            logger.info("Connecting to simulator %s", url)
            async with websockets.connect(url) as ws:
                logger.info("Simulator connected")
                async for raw in ws:
                    try:
                        data = json.loads(raw)
                        frame = SimulatorFrame.model_validate(data)
                    except Exception as exc:
                        logger.warning("Bad simulator frame: %s", exc)
                        continue

                    snap = _should_snapshot(frame.locomotive_id, snap_iv)
                    try:
                        async with async_session() as session:
                            provider = ServiceProvider(session)
                            payload = await apply_simulator_frame(
                                provider, frame, write_snapshot=snap
                            )
                            await session.commit()
                    except Exception as exc:
                        logger.exception("Telemetry ingest failed: %s", exc)
                        continue

                    await broadcast_telemetry(payload)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Simulator link lost (%s); retry in %ss", exc, delay)
            await asyncio.sleep(delay)
