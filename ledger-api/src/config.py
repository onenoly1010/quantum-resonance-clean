"""Configuration management for Ledger API."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ledger_db"
    
    # API Settings
    API_SECRET_KEY: str = "change-this-to-a-secure-random-string"
    API_TITLE: str = "Ledger API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    
    # Authentication
    AUTH_ENABLED: bool = True
    JWT_SECRET: str = "change-this-to-a-secure-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Treasury Settings
    DEFAULT_CURRENCY: str = "USD"
    TREASURY_ACCOUNT_PREFIX: str = "TRS"
    
    # Reconciliation
    AUTO_RECONCILE: bool = False
    RECONCILIATION_THRESHOLD: float = 0.01
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
