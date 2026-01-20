"""
Affiliate Copywriter OS - Configuration
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os
from pathlib import Path


# Ensure data directory exists for persistent storage
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default database path in data directory
DEFAULT_DB_PATH = f"sqlite+aiosqlite:///{DATA_DIR}/affiliate_copywriter.db"


class Settings(BaseSettings):
    # AI Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: Literal["openai", "anthropic"] = "anthropic"
    
    # Database - uses DATA_DIR for persistence
    database_url: str = DEFAULT_DB_PATH
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Pre-configured niches
    default_niches: list[str] = ["Auto Insurance", "Home Insurance", "Refi"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
