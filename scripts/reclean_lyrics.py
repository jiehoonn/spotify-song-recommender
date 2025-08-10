from sqlalchemy.orm import sessionmaker
from src.database.models import Lyrics
from scripts.test_apis import clean_lyrics_for_nrc
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

lyrics_entries = session.query(Lyrics).all()
for entry in lyrics_entries:
    try:
        # Re-clean the lyrics
        new_cleaned = clean_lyrics_for_nrc(entry.cleaned_lyrics)
        entry.cleaned_lyrics = new_cleaned
        session.commit()
        print(f"Re-cleaned lyrics for song_id {entry.song_id}")
    except Exception as e:
        session.rollback()
        print(f"Error re-cleaning lyrics for song_id {entry.song_id}: {e}")

session.close()