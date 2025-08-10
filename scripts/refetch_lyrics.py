from sqlalchemy.orm import sessionmaker
from src.database.models import Song, Lyrics
from scripts.test_apis import clean_lyrics_for_nrc
import lyricsgenius
from requests.exceptions import RequestException, Timeout, ConnectionError
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import time

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Increase timeout and add retries
genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"), timeout=30, retries=3)

lyrics_entries = session.query(Lyrics).all()
for entry in lyrics_entries:
    song = session.query(Song).filter_by(id=entry.song_id).first()
    if not song:
        print(f"Song with id {entry.song_id} not found.")
        continue

    for attempt in range(3):
        try:
            print(f"Refetching lyrics for: {song.spotify_title} by {song.spotify_artist} (attempt {attempt+1})")
            genius_song = genius.search_song(song.spotify_title, song.spotify_artist)
            if not genius_song or not genius_song.lyrics:
                print(f"Lyrics not found for {song.spotify_title} by {song.spotify_artist}.")
                entry.cleaned_lyrics = None
                session.commit()
                break

            cleaned = clean_lyrics_for_nrc(genius_song.lyrics)
            if cleaned:
                entry.cleaned_lyrics = cleaned
                session.commit()
                print(f"Updated lyrics for {song.spotify_title} by {song.spotify_artist}")
            else:
                print(f"Lyrics for {song.spotify_title} by {song.spotify_artist} are empty after cleaning.")
                entry.cleaned_lyrics = None
                session.commit()
            break  # Success, exit retry loop

        except (RequestException, Timeout, ConnectionError) as e:
            session.rollback()
            print(f"Network error processing {song.spotify_title} by {song.spotify_artist}: {e}")
            if attempt < 2:
                print("Retrying after 10 seconds...")
                time.sleep(10)
            else:
                print("Max retries reached. Skipping this song.")
        except Exception as e:
            session.rollback()
            print(f"Error processing {song.spotify_title} by {song.spotify_artist}: {e}")
            break

session.close()