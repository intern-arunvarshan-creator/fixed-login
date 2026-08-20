from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "platform-admin-v2"
    database_url: str

    # Logging
    log_level: str = "INFO"
    log_to_console: bool = True
    log_to_file: bool = True
    log_file: str = "logs/app_logs/platform-admin-v2.log"
    log_file_max_bytes: int = 10_000_000
    log_file_backup_count: int = 5

    # Tracing
    tracing_enabled: bool = False
    tracing_service_name: str = "platform-admin-v2"
    tracing_otlp_endpoint: str | None = None
    tracing_sample_rate: float = 1.0
    tracing_log_to_file: bool = True
    tracing_log_file: str = "logs/trace_logs/traces.log"
    tracing_log_to_console: bool = False

    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7


settings = Settings()
