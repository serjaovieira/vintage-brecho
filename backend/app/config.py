"""
Configuration module for Vintage Brechó Backend.
Loads environment variables using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres.umxkyzmccpmqazsldage:%40rthurVendas2026@aws-0-sa-east-1.pooler.supabase.com:5432/postgres",
        description="Database connection URL"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Supabase (Storage & Client)
    SUPABASE_URL: str = Field(
        default="https://umxkyzmccpmqazsldage.supabase.co",
        description="Supabase Project API URL"
    )
    SUPABASE_ANON_KEY: str = Field(
        default="",
        description="Supabase Public Anon Key"
    )
    SUPABASE_BUCKET: str = Field(
        default="brecho-photos",
        description="Storage bucket for piece photographs"
    )

    # Mercado Pago
    MERCADO_PAGO_PUBLIC_KEY: str = Field(
        default="TEST-21ac0ed2-2543-4222-aeaa-c3a628a7e353",
        description="Mercado Pago Public Key (Sandbox/Production)"
    )
    MERCADO_PAGO_ACCESS_TOKEN: str = Field(
        default="TEST-3858496967033964-092717-bb6348b2a247ce617009d180df433186-280525097",
        description="Mercado Pago Access Token"
    )

    # Server & Business Settings
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    FIXED_SHIPPING_PRICE: float = 15.00
    STORE_WHATSAPP: str = "17981668413"
    STORE_PHONE_DISPLAY: str = "(17) 98166-8413"

    @property
    def async_database_url(self) -> str:
        """
        Ensures the SQLAlchemy asyncpg driver scheme is present.
        Converts 'postgresql://' or 'postgres://' to 'postgresql+asyncpg://'.
        Preserves or converts SQLite URLs for async testing (e.g. 'sqlite+aiosqlite:///').
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite:///") and not url.startswith("sqlite+aiosqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return url


settings = Settings()
