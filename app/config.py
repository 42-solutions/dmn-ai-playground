from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Settings
    app_name: str = "AI Chat API"
    version: str = "1.0.0"

    # AI Settings
    anthropic_api_key: str
    gemini_api_key: str

    claude_model: str = "claude-3-5-sonnet-20241022"
    google_model: str = "gemini-2.5-flash"

    default_model: str = google_model
    max_tokens: int = 1024
    temperature: float = 0.7

    # Server Settings
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
