"""Browser WebSocket fan-out for processed telemetry."""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket

_clients: set[WebSocket] = set()
_latest_slot: list[dict[str, Any] | None] = [None]


async def register_browser_ws(ws: WebSocket) -> None:
    await ws.accept()
    subscribe_browser_ws(ws)


def subscribe_browser_ws(ws: WebSocket) -> None:
    """Register a client that was already accepted (e.g. after WebSocket auth)."""
    _clients.add(ws)


def unregister_browser_ws(ws: WebSocket) -> None:
    _clients.discard(ws)


def get_latest_telemetry() -> dict[str, Any] | None:
    return _latest_slot[0]


async def broadcast_telemetry(payload: dict[str, Any]) -> None:
    _latest_slot[0] = payload
    text = json.dumps(payload, default=str)
    dead: list[WebSocket] = []
    for client in list(_clients):
        try:
            await client.send_text(text)
        except Exception:
            dead.append(client)
    for ws in dead:
        _clients.discard(ws)
