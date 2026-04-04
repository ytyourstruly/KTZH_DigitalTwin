from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.telemetry_hub import (
    get_latest_telemetry,
    register_browser_ws,
    unregister_browser_ws,
)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/latest")
async def telemetry_latest() -> dict[str, Any] | None:
    """Last ingested frame (same JSON shape as ``/telemetry/stream``). ``null`` until first message."""
    return get_latest_telemetry()


@router.websocket("/stream")
async def telemetry_stream(ws: WebSocket) -> None:
    """Live telemetry processed by the backend (after DB persist)."""
    await register_browser_ws(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        unregister_browser_ws(ws)
