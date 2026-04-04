from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, hash_token, new_opaque_token, verify_password
from app.models.auth import AuthSession, User, UserRole
from app.services.auth.auth_session_service import AuthSessionService
from app.services.auth.user_service import UserService


class AuthenticationService:
    """Login, session validation, and logout using ``auth.sessions`` + opaque bearer tokens."""

    __slots__ = ("_users", "_sessions", "_ttl_hours")

    def __init__(
        self,
        users: UserService,
        sessions: AuthSessionService,
        *,
        session_ttl_hours: float,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._ttl_hours = session_ttl_hours

    async def register(self, username: str, email: str, password: str) -> User:
        if await self._users.get_by_username(username):
            raise ConflictError("Username already taken")
        if await self._users.get_by_email(email):
            raise ConflictError("Email already registered")
        user = User(
            username=username.strip(),
            email=email.strip(),
            password_hash=hash_password(password),
            role=UserRole.viewer,
            is_active=True,
        )
        try:
            await self._users.register(user)
        except IntegrityError:
            raise ConflictError("Username or email already registered") from None
        return user

    async def login(
        self,
        username: str,
        password: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, datetime]:
        user = await self._users.get_by_username(username)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid username or password")
        raw, digest = new_opaque_token()
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=self._ttl_hours)
        row = AuthSession(
            user_id=user.id,
            token_hash=digest,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        await self._sessions.create(row)
        return raw, expires_at

    async def authenticate(self, raw_token: str) -> User | None:
        digest = hash_token(raw_token)
        row = await self._sessions.get_by_token_hash(digest)
        if row is None:
            return None
        if row.revoked_at is not None:
            return None
        now = datetime.now(UTC)
        exp = row.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp <= now:
            return None
        user = await self._users.get_by_id(row.user_id)
        if user is None or not user.is_active:
            return None
        return user

    async def logout(self, raw_token: str) -> None:
        digest = hash_token(raw_token)
        row = await self._sessions.get_by_token_hash(digest)
        if row is None or row.revoked_at is not None:
            return
        row.revoked_at = datetime.now(UTC)
