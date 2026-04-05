from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps import AuthenticationServiceDep, CurrentUserDep
from app.core.config import get_settings
from app.realtime.telemetry_hub import (
    get_latest_telemetry,
    subscribe_browser_ws,
    unregister_browser_ws,
)
from app.schemas.telemetry_live import TelemetryLiveOut

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def _telemetry_ws_token(ws: WebSocket) -> str | None:
    q = ws.query_params.get("token")
    if q:
        return q
    return ws.cookies.get(get_settings().session_cookie_name)


@router.get("/latest", response_model=TelemetryLiveOut | None)
async def telemetry_latest(_user: CurrentUserDep) -> TelemetryLiveOut | None:
    """Последний кадр (как по ``/telemetry/stream``). ``null``, пока ingest не отдал данные."""
    data = get_latest_telemetry()
    if data is None:
        return None
    return TelemetryLiveOut.model_validate(data)


@router.websocket("/stream")
async def telemetry_stream(
    websocket: WebSocket,
    auth: AuthenticationServiceDep,
) -> None:
    """Live telemetry. Cookie сессии или query ``?token=`` (тот же opaque-токен, что после login)."""
    await websocket.accept()
    token = _telemetry_ws_token(websocket)
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    user = await auth.authenticate(token)
    if user is None or not user.is_active:
        await websocket.close(code=1008, reason="Invalid or expired session")
        return
    subscribe_browser_ws(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        unregister_browser_ws(websocket)
