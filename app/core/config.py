"""
Application configuration and settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Service role key (for admin operations)
    SUPABASE_ANON_KEY: str  # Anonymous/public key (for RLS)
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # LLM (OpenAI)
    OPENAI_API_KEY: str
    LLM_MODEL: str = "gpt-4-turbo-preview"
    
    # App
    SECRET_KEY: str
    APP_ENV: str = "development"
    
    # Rubric
    BASE_RUBRIC_VERSION: str = "1.0.0"
    RULESET_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
