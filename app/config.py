from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    app_name: str = "AI Chat API"
    version: str = "1.0.0"
    
    # AI Settings
    anthropic_api_key: str
    default_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1024
    
    # Server Settings
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
