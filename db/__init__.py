"""
Database engine & session factory.
Single source of truth for DB connection.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://localhost/kinyan_crm"
    SECRET_KEY: str = "dev-secret"
    API_KEY: str = "dev-api-key"

    class Config:
        env_file = ".env"


settings = Settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency: yields a DB session."""
    async with SessionLocal() as session:
        yield session


async def init_db():
    """Create all tables (for dev/first deploy)."""
    from db.models import Base as _  # noqa: ensure models are imported
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
