import requests
import os

def get_spotify_access_token():
    """Authenticate and get a Spotify API access token."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    auth_response = requests.post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        auth=(client_id, client_secret)
    )
    auth_response.raise_for_status()
    return auth_response.json()['access_token']

def search_spotify_track_artist(song_title, artist_name):
    """Search Spotify for a track and artist."""
    access_token = get_spotify_access_token()
    query = f"{song_title} {artist_name}"
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": query,
        "type": "track,artist",
        "market": "US",
        "include_external": "audio"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()