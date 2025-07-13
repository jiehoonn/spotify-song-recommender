from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_URL: str = f"sqlite:///{os.path.join(os.getcwd(), 'data', 'playlist_ai.db')}"
    
    # Spotify API
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    SPOTIFY_REDIRECT_URI: Optional[str] = None
    
    # Performance
    MAX_PLAYLIST_LENGTH: int = 50
    SIMILARITY_THRESHOLD: float = 0.3
    TARGET_RESPONSE_TIME: float = 0.2  # 200ms
    
    # Rate Limiting
    SPOTIFY_REQUEST_DELAY: float = 0.1  # 100ms between requests
    DAILY_REQUEST_LIMIT: int = 1800  # Below 2000 limit
    
    # Cache Settings
    CACHE_TTL_HOURS: int = 24
    ENABLE_CACHING: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()