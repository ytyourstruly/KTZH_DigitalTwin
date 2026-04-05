import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from api import routes as api_routes
from utils.logging_config import setup_logging

from broadcaster import Broadcaster
from engine import SimulationEngine
logger = logging.getLogger("simulator.main")


CONFIG_PATH = Path(__file__).parent / "config.yaml"
 
def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)
 
config = load_config()
setup_logging(config)
 
sim_cfg = config.get("simulator", {})
LOCO_ID = sim_cfg.get("locomotive_id", "LOCO-0001")
HOST    = sim_cfg.get("host", "0.0.0.0")
PORT    = 8080

engine      = SimulationEngine(locomotive_id=LOCO_ID)
broadcaster = Broadcaster(engine=engine, config=config)
api_routes.register(broadcaster)



@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(broadcaster.run_broadcast_loop())
    logger.info(
        "Locomotive Simulator started — ws://localhost:%d/telemetry", PORT
    )
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Simulator stopped.")


app = FastAPI(
    title="Locomotive Telemetry Simulator",
    description=(
        "Standalone WebSocket service that mimics a real-time locomotive data stream. "
        "Supports NORMAL, DEGRADATION, SPIKE and FAILURE simulation modes."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
 
app.include_router(api_routes.router, tags=["Control API"])




@app.websocket("/telemetry")
async def telemetry_ws(ws: WebSocket):
    """
    Primary WebSocket endpoint.
    Connect and receive continuous JSON telemetry frames.
    """
    await broadcaster.connect(ws)
    try:
        # Keep connection alive; broadcaster pushes data from its loop
        while True:
            # Heartbeat: accept any incoming text (ignored) so the
            # connection isn't treated as idle by proxies
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WS error: %s", exc)
    finally:
        broadcaster.disconnect(ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        ws_ping_interval=20,
        ws_ping_timeout=20,
    )


    