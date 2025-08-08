import requests
import os

def get_reccobeats_multiple_tracks(spotify_ids):
    """
    Query the ReccoBeats GET multiple track endpoint using one or more Spotify track IDs.
    """
    base_url = os.getenv("RECCOBEATS_API_URL")
    headers = {'Accept': 'application/json'}
    ids_params = '&'.join([f'ids={sid}' for sid in spotify_ids])
    url = f"{base_url}/track?{ids_params}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_reccobeats_audio_features(reccobeats_id):
    """
    Get audio features for a track from ReccoBeats using its ID.
    """
    base_url = os.getenv("RECCOBEATS_API_URL")
    headers = {'Accept': 'application/json'}
    url = f"{base_url}/track/{reccobeats_id}/audio-features"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()