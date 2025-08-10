from sqlalchemy.orm import sessionmaker
from src.database.models import Song, Lyrics
from scripts.test_apis import clean_lyrics_for_nrc
import lyricsgenius
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"), timeout=15)

# List of missing song IDs (from your query)
missing_song_ids = [46, 71, 84, 127, 153, 240, 383, 387]

for song_id in missing_song_ids:
    song = session.query(Song).filter_by(id=song_id).first()
    if not song:
        print(f"Song with id {song_id} not found.")
        continue
    if session.query(Lyrics).filter_by(song_id=song.id).first():
        print(f"Lyrics already exist for {song.spotify_title} by {song.spotify_artist}")
        continue

    try:
        print(f"Trying: {song.spotify_title} by {song.spotify_artist}")
        genius_song = genius.search_song(song.spotify_title, song.spotify_artist)
        if not genius_song or not genius_song.lyrics:
            print(f"Lyrics not found for {song.spotify_title} by {song.spotify_artist}.")
            continue

        cleaned = clean_lyrics_for_nrc(genius_song.lyrics)
        lyrics_entry = Lyrics(song_id=song.id, cleaned_lyrics=cleaned)
        session.add(lyrics_entry)
        session.commit()
        print(f"Added lyrics for {song.spotify_title} by {song.spotify_artist}")

    except Exception as e:
        session.rollback()
        print(f"Error processing {song.spotify_title} by {song.spotify_artist}: {e}")

session.close()