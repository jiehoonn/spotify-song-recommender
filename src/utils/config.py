import os
from dotenv import load_dotenv
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """Load and return configuration from environment variables."""
    load_dotenv()  # Load environment variables from .env file
    
    return {
        # Database
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_NAME': os.getenv('DB_NAME'),
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
        'DB_PORT': os.getenv('DB_PORT'),
        
        # Last.fm API
        'LASTFM_API_KEY': os.getenv('LASTFM_API_KEY'),
        'LASTFM_SHARED_SECRET': os.getenv('LASTFM_SHARED_SECRET'),
        'LASTFM_API_URL': os.getenv('LASTFM_API_URL'),
        
        # ReccoBeats API
        'RECCOBEATS_API_URL': os.getenv('RECCOBEATS_API_URL'),
        
        # Spotify API
        'SPOTIFY_CLIENT_ID': os.getenv('SPOTIFY_CLIENT_ID'),
        'SPOTIFY_CLIENT_SECRET': os.getenv('SPOTIFY_CLIENT_SECRET'),
        
        # Genius API
        'GENIUS_CLIENT_ID': os.getenv('GENIUS_CLIENT_ID'),
        'GENIUS_CLIENT_SECRET': os.getenv('GENIUS_CLIENT_SECRET'),
        'GENIUS_ACCESS_TOKEN': os.getenv('GENIUS_ACCESS_TOKEN')
    }