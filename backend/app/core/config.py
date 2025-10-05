"""
Configuration management using pydantic-settings.
Reads from .env file and environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # LLM Provider
    LLM_PROVIDER: Literal["openai", "claude", "deepseek"] = "openai"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    # Priority Policy
    PRIORITY_POLICY: Literal["eisenhower", "fifo"] = "eisenhower"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

