"""
Application configuration settings using Pydantic Settings.
Loads from environment variables with sensible defaults.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Maintenance Debt Index (MDI)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/mdi_db",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for Celery"
    )
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")
    
    # Debt Calculation Parameters
    DEFAULT_DECAY_RATE: float = Field(
        default=0.02,
        description="Daily compound decay rate (2% per day)"
    )
    MAX_DEBT_MULTIPLIER: float = Field(
        default=10.0,
        description="Maximum debt multiplier cap"
    )
    
    # Asset Type SLA Days
    SLA_ROAD_DAYS: int = 14
    SLA_DRAIN_DAYS: int = 7
    SLA_STREETLIGHT_DAYS: int = 3
    SLA_BRIDGE_DAYS: int = 21
    SLA_SIDEWALK_DAYS: int = 10
    SLA_DEFAULT_DAYS: int = 7
    
    # MDI Score Thresholds
    MDI_EXCELLENT_THRESHOLD: int = 90
    MDI_GOOD_THRESHOLD: int = 70
    MDI_FAIR_THRESHOLD: int = 50
    MDI_POOR_THRESHOLD: int = 30
    
    # External APIs
    MAPBOX_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Asset type to SLA mapping
def get_sla_days(asset_type: str, settings: Settings = None) -> int:
    """Get SLA days for a given asset type."""
    if settings is None:
        settings = get_settings()
    
    sla_mapping = {
        "road": settings.SLA_ROAD_DAYS,
        "drain": settings.SLA_DRAIN_DAYS,
        "streetlight": settings.SLA_STREETLIGHT_DAYS,
        "bridge": settings.SLA_BRIDGE_DAYS,
        "sidewalk": settings.SLA_SIDEWALK_DAYS,
    }
    return sla_mapping.get(asset_type.lower(), settings.SLA_DEFAULT_DAYS)


# Severity multipliers for repair costs
SEVERITY_MULTIPLIERS = {
    "low": 1.0,
    "medium": 1.5,
    "high": 2.0,
    "critical": 3.0,
}
