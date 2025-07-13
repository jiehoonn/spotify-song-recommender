import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler
from config.settings import settings

def get_spotify_client():
    # Ensure cache directory exists
    cache_dir = os.path.join(os.getcwd(), 'data', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create custom cache handler with our desired path
    cache_path = os.path.join(cache_dir, '.cache')
    cache_handler = CacheFileHandler(cache_path=cache_path)
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        cache_handler=cache_handler
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)