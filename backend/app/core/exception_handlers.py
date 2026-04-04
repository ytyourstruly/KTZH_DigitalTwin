import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from app.core.exceptions import AppError

logger = logging.getLogger("app.errors")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def logged_http_exception(request: Request, exc: HTTPException) -> Response:
        logger.info(
            "http_exception status=%s path=%s detail=%r",
            exc.status_code,
            request.url.path,
            exc.detail,
        )
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def logged_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "validation_error path=%s errors=%s",
            request.url.path,
            exc.errors(),
        )
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.info(
            "app_error code=%s status=%s path=%s message=%r",
            exc.code,
            exc.status_code,
            request.url.path,
            exc.message,
        )
        body: dict[str, str] = {"detail": exc.message, "code": exc.code}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception path=%s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
