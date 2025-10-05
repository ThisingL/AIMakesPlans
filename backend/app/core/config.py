"""
Configuration management using pydantic-settings.
Reads from .env file and environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import os
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # LLM Provider
    LLM_PROVIDER: Literal["openai", "claude", "deepseek", "siliconflow"] = "openai"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    MAX_TOKENS: int = 4000
    
    # API Keys (use OPENAI_API_KEY for compatibility with various providers)
    OPENAI_API_KEY: str = ""
    LLM_API_KEY: str = ""  # Alternative key name
    
    # Embedding (for future use)
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Priority Policy
    PRIORITY_POLICY: Literal["eisenhower", "fifo"] = "eisenhower"
    
    @property
    def api_key(self) -> str:
        """Get API key, preferring OPENAI_API_KEY for compatibility."""
        return self.OPENAI_API_KEY or self.LLM_API_KEY


# Global settings instance
settings = Settings()

