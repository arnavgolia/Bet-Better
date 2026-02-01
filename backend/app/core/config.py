"""
Core configuration management using Pydantic Settings.
Loads environment variables with validation and type safety.
"""

from typing import List, Optional
from pydantic import Field, validator, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    All settings are validated at startup to catch configuration errors early.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "SmartParlay"
    app_env: str = "development"
    debug: bool = False
    api_version: str = "v1"
    secret_key: str = Field(..., min_length=32)
    allowed_origins: List[str] = ["http://localhost:3000"]

    # Database
    database_url: PostgresDsn
    database_pool_size: int = 20
    database_max_overflow: int = 0

    # Redis
    redis_url: RedisDsn
    redis_cache_ttl: int = 3600

    # Odds Data Providers
    odds_api_key: Optional[str] = None
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"
    sportsdata_api_key: Optional[str] = None
    betfair_app_key: Optional[str] = None

    # Weather API
    weather_api_key: Optional[str] = None
    weather_api_base_url: str = "https://api.openweathermap.org/data/2.5"

    # GeoIP
    geoip_db_path: str = "/usr/share/GeoIP/GeoLite2-City.mmdb"

    # JAX Configuration
    jax_enable_x64: bool = True
    jax_platform_name: str = "cpu"

    # Simulation Parameters
    default_simulation_runs: int = 10000
    simulation_timeout_ms: int = 500
    default_nu_parameter: float = 5.0

    # Cache TTLs (seconds)
    odds_cache_ttl: int = 60
    marginals_cache_ttl: int = 86400  # 24 hours
    correlation_matrix_cache_ttl: int = 604800  # 7 days
    geo_cache_ttl: int = 3600  # 1 hour

    # Rate Limiting
    rate_limit_free_tier: int = 60
    rate_limit_pro_tier: int = 300

    # Kafka/Redpanda
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "smartparlay-backend"

    # Monitoring
    prometheus_port: int = 9090
    log_level: str = "INFO"

    # Affiliate IDs
    draftkings_affiliate_id: Optional[str] = None
    fanduel_affiliate_id: Optional[str] = None
    betmgm_affiliate_id: Optional[str] = None

    # Feature Flags
    enable_websocket_odds: bool = False
    enable_steam_detection: bool = True
    enable_sentiment_analysis: bool = False
    enable_live_betting: bool = False

    # Security
    cors_allow_credentials: bool = True
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Celery
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn

    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return str(self.database_url).replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


# Global settings instance
settings = Settings()
