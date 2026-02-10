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
    
    # Dev mode: skip authentication
    DEV_SKIP_AUTH: bool = False

    # JWT
    JWT_SECRET_KEY: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/auth/google/callback"

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Kinyan CRM"

    # Nedarim Plus API
    NEDARIM_API_URL: str = "https://api.nedarimplus.co.il/v1"
    NEDARIM_API_KEY: str = ""
    NEDARIM_MOSAD_ID: str = ""
    NEDARIM_WEBHOOK_SECRET: str = ""

    # Frontend URL (for reset links, welcome page, etc.)
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

    @property
    def async_database_url(self) -> str:
        """Convert Render's postgres:// to postgresql+asyncpg:// for async SQLAlchemy."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()

# Use async_database_url to ensure correct driver for Render deployments
engine = create_async_engine(settings.async_database_url, echo=False)
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
