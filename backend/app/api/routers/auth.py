from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import (
    AuthenticationServiceDep,
    CurrentUserDep,
    get_access_token,
)
from app.core.session_cookie import attach_session_cookie, clear_session_cookie
from app.models.auth import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    auth: AuthenticationServiceDep,
) -> User:
    return await auth.register(body.username, body.email, body.password)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    auth: AuthenticationServiceDep,
) -> LoginResponse:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token, expires_at = await auth.login(
        body.username,
        body.password,
        ip_address=ip,
        user_agent=ua,
    )
    attach_session_cookie(response, token, expires_at)
    return LoginResponse(expires_at=expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    token: Annotated[str, Depends(get_access_token)],
    auth: AuthenticationServiceDep,
) -> None:
    await auth.logout(token)
    clear_session_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUserDep) -> User:
    return user
