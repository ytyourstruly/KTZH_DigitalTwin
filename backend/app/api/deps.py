from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.db.session import async_session
from app.models.auth import User
from app.provider import ServiceProvider
from app.services.auth import AuthenticationService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_service_provider(session: AsyncSessionDep) -> ServiceProvider:
    return ServiceProvider(session)


ServiceProviderDep = Annotated[ServiceProvider, Depends(get_service_provider)]


def get_authentication_service(provider: ServiceProviderDep) -> AuthenticationService:
    return provider.authentication_service()


AuthenticationServiceDep = Annotated[
    AuthenticationService,
    Depends(get_authentication_service),
]

# Registers `http` + `bearer` in OpenAPI so Swagger UI shows **Authorize** on routes that use this dependency.
http_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="session_token",
    description=(
        "HttpOnly **session** cookie from **POST /api/v1/auth/login** (browser), "
        "or paste a bearer token for tools (e.g. copy cookie value from devtools). "
        "Swagger sends `Authorization: Bearer <token>`."
    ),
)


async def get_access_token(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(http_bearer),
    ],
) -> str:
    if credentials is not None and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    cookie_name = get_settings().session_cookie_name
    from_cookie = request.cookies.get(cookie_name)
    if from_cookie:
        return from_cookie
    raise UnauthorizedError("Not authenticated")


async def get_current_user(
    token: Annotated[str, Depends(get_access_token)],
    auth: AuthenticationServiceDep,
) -> User:
    user = await auth.authenticate(token)
    if user is None:
        raise UnauthorizedError("Invalid or expired session")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]