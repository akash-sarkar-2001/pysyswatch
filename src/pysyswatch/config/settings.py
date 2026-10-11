from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API & Database
    api_key: str | None = None
    database_url: str = "sqlite:///pysyswatch.db"
    log_level: str = "INFO"
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]
    rate_limit_per_minute: int = 60

    # Daemon Configuration
    collection_interval: int = 10

    # Diagnostic Thresholds (Percentages)
    cpu_warning_threshold: float = 80.0
    cpu_critical_threshold: float = 95.0
    memory_warning_threshold: float = 85.0
    memory_critical_threshold: float = 95.0
    disk_warning_threshold: float = 85.0
    disk_critical_threshold: float = 95.0

    # Retention & Alerts
    metrics_retention_days: int = 7
    alert_webhook_url: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="PYSYSWATCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
