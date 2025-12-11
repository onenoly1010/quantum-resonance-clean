"""
Configuration module for Ledger API.
Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://ledger_user:password@localhost:5432/ledger_db"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    ALLOW_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOW_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOW_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
