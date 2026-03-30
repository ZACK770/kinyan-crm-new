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
    SMTP_FROM_NAME: str = "קניין הוראה - מחלקת רישום"

    # Nedarim Plus API
    NEDARIM_API_URL: str = "https://api.nedarimplus.co.il/v1"
    NEDARIM_API_KEY: str = ""
    NEDARIM_MOSAD_ID: str = ""
    NEDARIM_WEBHOOK_SECRET: str = ""

    # Yemot / Call2All API (for tzintuk verification)
    YEMOT_API_BASE_URL: str = "https://www.call2all.co.il/ym/api/"
    YEMOT_TOKEN: str = ""
    YEMOT_TZINTUK_TIMEOUT_SECONDS: float = 9.0

    # Frontend URL (for reset links, welcome page, etc.)
    FRONTEND_URL: str = "http://localhost:5173"

    # Cloudflare R2 Storage
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

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
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={
        "timeout": 10,
        "command_timeout": 30,
    }
)
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
