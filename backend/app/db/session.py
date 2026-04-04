from app.core.config import get_settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_settings = get_settings()

engine = create_async_engine(
    _settings.sqlalchemy_url,
    echo=True,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

