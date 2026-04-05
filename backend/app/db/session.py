from app.core.config import get_settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_settings = get_settings()

_async_url = _settings.sqlalchemy_url
if _async_url.startswith("postgresql+psycopg://"):
    _async_url = _async_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
elif _async_url.startswith("postgresql://"):
    _async_url = _async_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    _async_url,
    echo=True,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

