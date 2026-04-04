"""
Legacy standalone demo (FastAPI on :9000). Production wiring lives in the backend:

  backend/app/realtime/simulator_client.py  — ingest loop
  backend/app/realtime/telemetry_hub.py     — browser fan-out
  backend/app/api/routers/telemetry.py      — ``/api/v1/telemetry/stream``

Enable with ``SIMULATOR_INGEST_ENABLED=true`` and run the simulator on ``SIMULATOR_WS_URL``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional, Set

import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger("backend.simulator_client")

SIMULATOR_WS_URL = "ws://localhost:8080/telemetry"
RECONNECT_DELAY_SEC = 3


# ---------------------------------------------------------------------------
# Telemetry model (mirrors simulator output)
# ---------------------------------------------------------------------------

class TelemetryFrame(BaseModel):
    timestamp:      str
    locomotive_id:  str
    speed:          Optional[float] = None
    fuel_level:     Optional[float] = None
    engine_temp:    Optional[float] = None
    oil_pressure:   Optional[float] = None
    voltage:        Optional[float] = None
    current:        Optional[float] = None
    error_codes:    list[str] = []
    health_hint:    Optional[str] = "ok"
    mode:           Optional[str] = None


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

latest_frame: Optional[TelemetryFrame] = None
frame_queue: asyncio.Queue[TelemetryFrame] = asyncio.Queue(maxsize=500)
browser_clients: Set[WebSocket] = set()


# ---------------------------------------------------------------------------
# Simulator WebSocket client (auto-reconnecting)
# ---------------------------------------------------------------------------

async def simulator_client_loop() -> None:
    """
    Connects to the simulator, reads frames forever, and:
      - updates `latest_frame` (for REST polling)
      - puts frames on `frame_queue`  (for DB writes)
      - fans out to connected browser WebSockets
    """
    global latest_frame

    while True:
        try:
            logger.info("Connecting to simulator at %s …", SIMULATOR_WS_URL)
            async with websockets.connect(SIMULATOR_WS_URL) as ws:
                logger.info("Connected to simulator ✓")
                async for raw in ws:
                    try:
                        data = json.loads(raw)
                        frame = TelemetryFrame(**data)
                    except Exception as exc:
                        logger.warning("Parse error: %s | raw=%s", exc, raw[:120])
                        continue

                    latest_frame = frame

                    # Non-blocking put (drop if queue is full to avoid back-pressure)
                    if not frame_queue.full():
                        frame_queue.put_nowait(frame)

                    # Fan out to browser clients
                    await _fan_out(frame)

        except (websockets.ConnectionClosed, OSError) as exc:
            logger.warning("Simulator disconnected (%s). Reconnecting in %ds …",
                           exc, RECONNECT_DELAY_SEC)
            await asyncio.sleep(RECONNECT_DELAY_SEC)
        except Exception as exc:
            logger.error("Unexpected error: %s. Reconnecting …", exc)
            await asyncio.sleep(RECONNECT_DELAY_SEC)


async def _fan_out(frame: TelemetryFrame) -> None:
    dead = []
    payload = frame.model_dump_json()
    for ws in list(browser_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        browser_clients.discard(ws)


# ---------------------------------------------------------------------------
# DB writer worker (plug in your actual DB session here)
# ---------------------------------------------------------------------------

async def db_writer_worker() -> None:
    """
    Drains frame_queue and writes to PostgreSQL.
    Replace the body with your SQLAlchemy / asyncpg calls.
    """
    while True:
        frame = await frame_queue.get()
        try:
            await _write_to_db(frame)
        except Exception as exc:
            logger.error("DB write failed: %s", exc)
        finally:
            frame_queue.task_done()


async def _write_to_db(frame: TelemetryFrame) -> None:
    """Stub — replace with your actual async DB insert."""
    # Example using asyncpg / SQLAlchemy async session:
    #
    # async with async_session() as session:
    #     session.add(TelemetryRecord(**frame.model_dump()))
    #     await session.commit()
    #
    logger.debug("Would write to DB: loco=%s speed=%s health=%s",
                 frame.locomotive_id, frame.speed, frame.health_hint)


# ---------------------------------------------------------------------------
# FastAPI integration
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start simulator client and DB writer as background tasks
    client_task = asyncio.create_task(simulator_client_loop())
    writer_task = asyncio.create_task(db_writer_worker())
    yield
    client_task.cancel()
    writer_task.cancel()


app = FastAPI(title="Locomotive Backend", lifespan=lifespan)


@app.get("/telemetry/latest", response_model=Optional[TelemetryFrame])
async def get_latest():
    """Return the most recent telemetry frame (for REST polling)."""
    return latest_frame


@app.websocket("/telemetry/stream")
async def browser_stream(ws: WebSocket):
    """
    Fan-out WebSocket endpoint for browser / frontend clients.
    The backend receives from the simulator and relays here.
    """
    await ws.accept()
    browser_clients.add(ws)
    logger.info("Browser client connected — total=%d", len(browser_clients))
    try:
        while True:
            await ws.receive_text()   # keep alive
    except WebSocketDisconnect:
        pass
    finally:
        browser_clients.discard(ws)
        logger.info("Browser client disconnected")


# ---------------------------------------------------------------------------
# Run (dev only)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend_client:app", host="0.0.0.0", port=9000, reload=True)