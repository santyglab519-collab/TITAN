from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix=""  # Matches exact variable names or defaults
    )

    # General configuration
    app_name: str = "TITÁN Core"
    environment: str = "development"
    log_level: str = "INFO"

    # Database configuration
    database_url: str = "postgresql+asyncpg://titan:titan_password@localhost:5432/titan_db"

    # Observability
    prometheus_port: int = 8000

    # LLM Providers configuration
    openai_api_key: str = "mock-openai-api-key"
    anthropic_api_key: str = "mock-anthropic-api-key"

settings = Settings()
