"""
Ledger API Configuration
Loads environment variables and provides application settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ledger_db",
        description="Async PostgreSQL database URL"
    )
    
    # Authentication - CRITICAL: Store actual secret in Supabase secrets or encrypted vault
    GUARDIAN_JWT_SECRET: str = Field(
        default="dev-secret-change-in-production",
        description="JWT signing secret - MUST be stored securely in production"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT token expiration in hours")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host binding")
    API_PORT: int = Field(default=8001, description="API port")
    API_RELOAD: bool = Field(default=False, description="Enable auto-reload in development")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Wallet Configuration
    # SECURITY: All wallet addresses/keys MUST be stored in Supabase secrets or encrypted vault
    # Never commit actual wallet addresses to the repository
    TREASURY_WALLET_REF: Optional[str] = Field(
        default=None,
        description="Reference to treasury wallet in secure vault (e.g., ${SUPABASE_SECRET:treasury_wallet})"
    )
    
    # API Metadata
    API_TITLE: str = Field(default="Ledger API", description="API title")
    API_VERSION: str = Field(default="1.0.0", description="API version")
    API_DESCRIPTION: str = Field(
        default="Single source of truth for ledger transactions, allocations, and treasury management",
        description="API description"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
