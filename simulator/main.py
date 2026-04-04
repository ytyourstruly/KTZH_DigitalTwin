from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from api import routes as api_routes

logger = logging.getLogger("simulator.main")


CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

config = load_config()

sim_cfg = config.get("simulator", {})
LOCO_ID = sim_cfg.get("locomotive_id", "LOCO-0001")
HOST    = sim_cfg.get("host", "0.0.0.0")
PORT    = int(os.environ.get("PORT", sim_cfg.get("port", 9001)))



app = FastAPI(
    title="Locomotive Telemetry Simulator",
    description=(
        "Standalone WebSocket service that mimics a real-time locomotive data stream. "
        "Supports NORMAL, DEGRADATION, SPIKE and FAILURE simulation modes."
    ),
    version="1.0.0",
)

app.include_router(api_routes.router, tags=["Control API"])

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