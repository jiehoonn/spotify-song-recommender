import os
import time
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.api.lastfm import get_lastfm_top_n_tracks
from src.api.spotify import search_spotify_track_artist
from src.api.reccobeats import get_reccobeats_multiple_tracks, get_reccobeats_audio_features
from src.database.models import Song

load_dotenv()

# Database connection setup
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    print("Fetching top 500 charting songs from Last.fm...")
    tracks = get_lastfm_top_n_tracks(n=500, per_page=100)

    session = SessionLocal()

    for idx, track in enumerate(tracks, 1):
        song_title = track.get("name")
        artist_name = track.get("artist", {}).get("name")
        print(f"\n=== [{idx}] {song_title} by {artist_name} ===")

        # Spotify
        spotify_data = search_spotify_track_artist(song_title, artist_name)
        if not spotify_data['tracks']['items']:
            print("No Spotify track found. Skipping to next track.")
            continue
        spotify_track = spotify_data['tracks']['items'][0]
        spotify_id = spotify_track['id']

        # ReccoBeats
        try:
            reccobeats_tracks = get_reccobeats_multiple_tracks([spotify_id])
            if not (reccobeats_tracks.get('content') and len(reccobeats_tracks['content']) > 0):
                print("No ReccoBeats track found for this Spotify ID. Skipping to next track.")
                continue
            reccobeats_track = reccobeats_tracks['content'][0]
            reccobeats_id = reccobeats_track.get('id')
        except Exception as e:
            print(f"ReccoBeats API error: {e}. Skipping to next track.")
            continue

        # Audio Features
        try:
            audio_features = get_reccobeats_audio_features(reccobeats_id)
        except Exception as e:
            print(f"Could not retrieve audio features for this track: {e}")
            continue

        # === DUPLICATE CHECK GOES HERE ===
        existing = session.query(Song).filter_by(spotify_id=spotify_id).first()
        if existing:
            print("Song already exists in database. Skipping.")
            continue

        # Insert into database
        try:
            song = Song(
                lastfm_mbid=track.get("mbid"),
                lastfm_title=song_title,
                lastfm_artist=artist_name,
                lastfm_url=track.get("url"),
                lastfm_playcount=int(track.get("playcount") or 0),
                lastfm_listeners=int(track.get("listeners") or 0),
                spotify_id=spotify_id,
                spotify_title=spotify_track.get("name"),
                spotify_artist=spotify_track['artists'][0].get("name") if spotify_track.get("artists") else None,
                spotify_album=spotify_track.get("album", {}).get("name"),
                spotify_popularity=spotify_track.get("popularity"),
                spotify_duration_ms=spotify_track.get("duration_ms"),
                spotify_url=spotify_track.get("external_urls", {}).get("spotify"),
                reccobeats_id=reccobeats_id,
                acousticness=audio_features.get("acousticness"),
                danceability=audio_features.get("danceability"),
                energy=audio_features.get("energy"),
                instrumentalness=audio_features.get("instrumentalness"),
                liveness=audio_features.get("liveness"),
                loudness=audio_features.get("loudness"),
                speechiness=audio_features.get("speechiness"),
                tempo=audio_features.get("tempo"),
                valence=audio_features.get("valence"),
            )
            session.add(song)
            session.commit()
            print("Song added to database.")
        except Exception as e:
            session.rollback()
            print(f"Database insert error: {e}")

        time.sleep(2)

    session.close()
    print("Done.")

if __name__ == "__main__":
    main()