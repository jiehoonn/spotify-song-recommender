from sqlalchemy.orm import sessionmaker
from src.database.models import Song, Lyrics
from scripts.test_apis import clean_lyrics_for_nrc
import lyricsgenius
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"), timeout=15)

# Find all Lyrics entries with empty cleaned_lyrics
empty_lyrics_entries = session.query(Lyrics).filter(
    (Lyrics.cleaned_lyrics == None) | (Lyrics.cleaned_lyrics == '')
).all()

for entry in empty_lyrics_entries:
    song = session.query(Song).filter_by(id=entry.song_id).first()
    if not song:
        print(f"Song with id {entry.song_id} not found.")
        continue

    try:
        print(f"Refetching lyrics for: {song.spotify_title} by {song.spotify_artist}")
        genius_song = genius.search_song(song.spotify_title, song.spotify_artist)
        if not genius_song or not genius_song.lyrics:
            print(f"Lyrics not found for {song.spotify_title} by {song.spotify_artist}.")
            continue

        cleaned = clean_lyrics_for_nrc(genius_song.lyrics)
        if cleaned:
            entry.cleaned_lyrics = cleaned
            session.commit()
            print(f"Updated lyrics for {song.spotify_title} by {song.spotify_artist}")
        else:
            print(f"Lyrics for {song.spotify_title} by {song.spotify_artist} are still empty after cleaning.")

    except Exception as e:
        session.rollback()
        print(f"Error processing {song.spotify_title} by {song.spotify_artist}: {e}")