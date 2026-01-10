"""
Application configuration using Pydantic settings.
Environment-based configuration for all reliability patterns.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "HomeRack API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./homerack.db", description="Database connection URL")
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Connection pool timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Recycle connections after seconds")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries (for debugging)")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_DEFAULT: str = Field(default="300/hour", description="Default rate limit")
    RATE_LIMIT_ANONYMOUS: str = Field(default="100/hour", description="Rate limit for anonymous users")
    RATE_LIMIT_THERMAL_ANALYSIS: str = Field(default="10/minute", description="Rate limit for thermal analysis")
    RATE_LIMIT_BULK_OPERATIONS: str = Field(default="5/minute", description="Rate limit for bulk operations")
    RATE_LIMIT_REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for distributed rate limiting")

    # Timeouts (in seconds)
    REQUEST_TIMEOUT_DEFAULT: int = Field(default=30, description="Default request timeout")
    REQUEST_TIMEOUT_HEALTH: int = Field(default=5, description="Health check timeout")
    REQUEST_TIMEOUT_THERMAL: int = Field(default=60, description="Thermal analysis timeout")
    REQUEST_TIMEOUT_OPTIMIZATION: int = Field(default=120, description="Optimization timeout")
    REQUEST_TIMEOUT_BULK: int = Field(default=60, description="Bulk operation timeout")

    # Retry Configuration
    RETRY_ENABLED: bool = Field(default=True, description="Enable retry mechanism")
    RETRY_MAX_ATTEMPTS: int = Field(default=5, description="Maximum retry attempts")
    RETRY_MAX_DELAY: int = Field(default=10, description="Maximum delay between retries (seconds)")
    RETRY_EXPONENTIAL_BASE: float = Field(default=2.0, description="Exponential backoff base")
    RETRY_JITTER: bool = Field(default=True, description="Add jitter to retry delays")

    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED: bool = Field(default=True, description="Enable circuit breaker")
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, description="Failures before opening circuit")
    CIRCUIT_BREAKER_TIMEOUT: int = Field(default=30, description="Timeout before testing recovery (seconds)")
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(default=60, description="Timeout in half-open state (seconds)")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or console")
    LOG_REQUEST_BODY: bool = Field(default=False, description="Log request bodies (may contain sensitive data)")
    LOG_RESPONSE_BODY: bool = Field(default=False, description="Log response bodies")
    LOG_SLOW_QUERY_THRESHOLD: float = Field(default=1.0, description="Log queries slower than this (seconds)")

    # Caching
    CACHE_ENABLED: bool = Field(default=True, description="Enable caching")
    CACHE_REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for caching")
    CACHE_TTL_THERMAL_ANALYSIS: int = Field(default=300, description="Thermal analysis cache TTL (seconds)")
    CACHE_TTL_DEVICE_SPECS: int = Field(default=3600, description="Device specs cache TTL (seconds)")
    CACHE_TTL_RACK_LAYOUT: int = Field(default=600, description="Rack layout cache TTL (seconds)")

    # Web Spec Fetching
    SPEC_FETCH_ENABLED: bool = Field(default=True, description="Enable automatic spec fetching")
    SPEC_FETCH_TIMEOUT: int = Field(default=30, description="Spec fetch timeout (seconds)")
    SPEC_FETCH_USER_AGENT: str = Field(
        default="HomeRack/1.0 (https://github.com/yourusername/homerack)",
        description="User agent for web requests"
    )
    SPEC_FETCH_MAX_PDF_SIZE_MB: int = Field(default=10, description="Maximum PDF size to download (MB)")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production", description="Secret key for signing")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration (minutes)")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
