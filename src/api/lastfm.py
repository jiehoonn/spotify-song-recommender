import requests
import os

def get_lastfm_top_tracks(limit=50):
    """Fetch top charting tracks from Last.fm."""
    api_key = os.getenv("LASTFM_API_KEY")
    base_url = os.getenv("LASTFM_API_URL")
    url = f"{base_url}?method=chart.gettoptracks&api_key={api_key}&format=json&limit={limit}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_lastfm_top_n_tracks(n=500, per_page=100):
    """Fetch top n charting tracks from Last.fm using pagination."""
    api_key = os.getenv("LASTFM_API_KEY")
    base_url = os.getenv("LASTFM_API_URL")
    all_tracks = []
    pages = (n + per_page - 1) // per_page  # Ceiling division

    for page in range(1, pages + 1):
        url = f"{base_url}?method=chart.gettoptracks&api_key={api_key}&format=json&limit={per_page}&page={page}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tracks = data.get("tracks", {}).get("track", [])
        all_tracks.extend(tracks)
        print(f"Fetched page {page}, got {len(tracks)} tracks.")

    return all_tracks[:n]