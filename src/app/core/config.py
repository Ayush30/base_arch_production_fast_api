from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "local"
    app_name: str = "marketplace-backend"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = Field(8000, ge=1, le=65535)
    app_docs_enabled: bool = True
    debug: bool = Field(False, validation_alias="APP_DEBUG")

    # Database
    database_url: str = "postgresql+asyncpg://marketplace:marketplace@localhost:5432/marketplace"

    # Primary (write) connection pool
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Read replica — leave empty to use primary for reads
    database_read_replica_url: str = ""

    # Read replica pool (only used when database_read_replica_url is non-empty)
    db_read_pool_size: int = 10
    db_read_max_overflow: int = 20
    db_read_pool_timeout: int = 30
    db_read_pool_recycle: int = 3600

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_algorithm: str = "RS256"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_private_key_path: str = "keys/private.pem"
    jwt_access_token_expire_minutes: int = 60

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "marketplace-backend"
    metrics_enabled: bool = True
    metrics_path: str = "/metrics"

    # Kafka — publishes audit events, consumed by audit-service. See
    # app/core/audit_client.py and app/kafka/constants.py for topic names.
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "marketplace-backend"

    # Marketplace: local adapters cannot be enabled in production.
    jwt_issuer: str = "marketplace"
    jwt_audience: str = "marketplace-mobile"
    refresh_token_days: int = Field(30, ge=1, le=90)
    local_payments_enabled: bool = True
    local_email_tokens_enabled: bool = True
    auth_rate_limit: int = Field(20, ge=1)
    rate_limit_enabled: bool = True
    kafka_enabled: bool = False
    cors_origins: list[str] = []
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver", "test"]
    supported_currencies: list[str] = ["USD"]
    commission_bps: int = Field(1000, ge=0, le=10000)
    checkout_expiry_minutes: int = Field(30, ge=1, le=1440)

    @model_validator(mode="after")
    def safe_production(self) -> Self:
        if self.app_env == "production":
            if self.local_payments_enabled or self.local_email_tokens_enabled or self.debug:
                raise ValueError("Production forbids local payment/email adapters and debug")
            if not self.rate_limit_enabled or "*" in self.allowed_hosts:
                raise ValueError("Production requires rate limiting and explicit allowed hosts")
        if self.jwt_algorithm != "RS256":
            raise ValueError("Only RS256 tokens are supported")
        if not self.supported_currencies or any(
            c not in {"USD", "EUR", "GBP", "JPY", "KWD"} for c in self.supported_currencies
        ):
            raise ValueError("Configure currencies listed in core/money.py")
        return self

    # Tenancy
    tenant_schema_prefix: str = "tenant_"
    shared_schema: str = "shared"

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
