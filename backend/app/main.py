import asyncio
from contextlib import asynccontextmanager
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.auth import router as auth_api_router
from app.api.routers.telemetry import router as telemetry_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.realtime.simulator_client import run_simulator_ingest_loop

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    ingest_task: asyncio.Task[None] | None = None
    if get_settings().simulator_ingest_enabled:
        ingest_task = asyncio.create_task(run_simulator_ingest_loop())
    yield
    if ingest_task is not None:
        ingest_task.cancel()
        try:
            await ingest_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="KTZH Digital Twin API",
    version="0.1.0",
    lifespan=lifespan,
)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)
    
app.include_router(auth_api_router, prefix="/api/v1")
app.include_router(telemetry_router, prefix="/api/v1")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/env-configs")
async def env_configs() -> dict[str, Any]:
    return {
        "session_ttl_hours": get_settings().session_ttl_hours,
        "session_cookie_name": get_settings().session_cookie_name,
        "session_cookie_path": get_settings().session_cookie_path,
        "session_cookie_domain": str(get_settings().session_cookie_domain),
        "session_cookie_secure": str(get_settings().session_cookie_secure),
        "session_cookie_samesite": get_settings().session_cookie_samesite,
        "postgres_user": get_settings().postgres_user,
        "postgres_password": get_settings().postgres_password,
        "postgres_host": get_settings().postgres_host,
        "postgres_port": get_settings().postgres_port,
        "postgres_db": get_settings().postgres_db,
        "simulator_ingest_enabled": get_settings().simulator_ingest_enabled,
        "simulator_ws_url": get_settings().simulator_ws_url,
        "simulator_reconnect_delay_sec": get_settings().simulator_reconnect_delay_sec,
        "telemetry_snapshot_interval_sec": get_settings().telemetry_snapshot_interval_sec,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
