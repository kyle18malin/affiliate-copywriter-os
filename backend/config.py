"""
Affiliate Copywriter OS - Configuration
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os
from pathlib import Path


def get_database_url():
    """
    Get database URL, supporting both PostgreSQL (Railway) and SQLite (local).
    Railway provides DATABASE_URL automatically when you add PostgreSQL.
    """
    db_url = os.environ.get("DATABASE_URL", "")
    
    # Railway PostgreSQL - convert postgres:// to postgresql+asyncpg://
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url:
        return db_url
    
    # Local SQLite fallback
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{data_dir}/affiliate_copywriter.db"


class Settings(BaseSettings):
    # AI Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: Literal["openai", "anthropic"] = "anthropic"
    
    # Database - auto-detects PostgreSQL (Railway) or SQLite (local)
    database_url: str = ""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Pre-configured niches
    default_niches: list[str] = ["Auto Insurance", "Home Insurance", "Refi"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set database URL if not provided
        if not self.database_url:
            self.database_url = get_database_url()


settings = Settings()
