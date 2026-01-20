"""
Affiliate Copywriter OS - Configuration
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os


class Settings(BaseSettings):
    # AI Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: Literal["openai", "anthropic"] = "anthropic"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./affiliate_copywriter.db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Pre-configured niches
    default_niches: list[str] = ["Auto Insurance", "Home Insurance", "Refi"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
