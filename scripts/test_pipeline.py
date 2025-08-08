import os
from dotenv import load_dotenv
from src.api.lastfm import get_lastfm_top_tracks
from src.api.spotify import search_spotify_track_artist
from src.api.reccobeats import get_reccobeats_multiple_tracks, get_reccobeats_audio_features
import json
import time

load_dotenv()

def main():
    print("Fetching top 50 charting songs from Last.fm...")
    lastfm_data = get_lastfm_top_tracks(limit=50)
    tracks = lastfm_data["tracks"]["track"]

    for idx, track in enumerate(tracks, 1):
        song_title = track.get("name")
        artist_name = track.get("artist", {}).get("name")
        print(f"\n=== [{idx}] {song_title} by {artist_name} ===")
        print("Last.fm Data:")
        print("  MBID:", track.get("mbid"))
        print("  Title:", song_title)
        print("  Artist:", artist_name)
        print("  URL:", track.get("url"))
        print("  Playcount:", track.get("playcount"))
        print("  Listeners:", track.get("listeners"))

        print("Testing Spotify API...")
        spotify_data = search_spotify_track_artist(song_title, artist_name)
        if spotify_data['tracks']['items']:
            spotify_track = spotify_data['tracks']['items'][0]
            spotify_id = spotify_track['id']
            print("Spotify Data:")
            print("  ID:", spotify_track.get("id"))
            print("  Title:", spotify_track.get("name"))
            print("  Artist:", spotify_track['artists'][0].get("name") if spotify_track.get("artists") else None)
            print("  Album:", spotify_track.get("album", {}).get("name"))
            print("  Popularity:", spotify_track.get("popularity"))
            print("  Duration (ms):", spotify_track.get("duration_ms"))
            print("  URL:", spotify_track.get("external_urls", {}).get("spotify"))
        else:
            print("No Spotify track found. Skipping to next track.")
            continue

        print("Testing ReccoBeats Multiple Track API...")
        try:
            reccobeats_tracks = get_reccobeats_multiple_tracks([spotify_id])
            if reccobeats_tracks.get('content') and len(reccobeats_tracks['content']) > 0:
                reccobeats_track = reccobeats_tracks['content'][0]
                reccobeats_id = reccobeats_track.get('id')
                print("ReccoBeats Data:")
                print("  ID:", reccobeats_id)
            else:
                print("No ReccoBeats track found for this Spotify ID. Skipping to next track.")
                continue
        except Exception as e:
            print(f"ReccoBeats API error: {e}. Skipping to next track.")
            continue

        print("Testing ReccoBeats Audio Features API...")
        try:
            audio_features = get_reccobeats_audio_features(reccobeats_id)
            print("Audio Features:")
            for feature in [
                "acousticness", "danceability", "energy", "instrumentalness", "liveness",
                "loudness", "speechiness", "tempo", "valence"
            ]:
                print(f"  {feature.capitalize()}: {audio_features.get(feature)}")
        except Exception as e:
            print(f"Could not retrieve audio features for this track: {e}")
            continue

        # Optional: Sleep to avoid hitting rate limits
        time.sleep(2)

if __name__ == "__main__":
    main()