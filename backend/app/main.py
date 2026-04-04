import asyncio
from contextlib import asynccontextmanager
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging
from app.api.routers.auth import router as auth_api_router
from app.middleware.request_logging import RequestLoggingMiddleware

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


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
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
