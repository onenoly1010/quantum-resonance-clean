"""Configuration management for Ledger API"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ledger_db"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_DEBUG: bool = False
    API_TITLE: str = "Ledger API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Double-entry bookkeeping system with allocation engine"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Guardian
    GUARDIAN_WALLET_ADDRESS: str = "jg4c...rgi"
    
    # Reconciliation
    RECONCILIATION_CRON_ENABLED: bool = True
    RECONCILIATION_INTERVAL_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
