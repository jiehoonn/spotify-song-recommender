from sqlalchemy.orm import sessionmaker
from src.database.models import Lyrics, Song
from sqlalchemy import create_engine
from langdetect import detect
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

for entry in session.query(Lyrics).all():
    if entry.cleaned_lyrics:
        try:
            lang = detect(entry.cleaned_lyrics)
            if lang != 'en':
                # Delete the lyrics row
                print(f"Deleting lyrics (lang={lang}) for song_id {entry.song_id}")
                session.delete(entry)
                # Delete the corresponding song row
                song = session.query(Song).filter_by(id=entry.song_id).first()
                if song:
                    print(f"Deleting song '{song.spotify_title}' by '{song.spotify_artist}' (id={song.id})")
                    session.delete(song)
                session.commit()
        except Exception as e:
            print(f"Error processing song_id {entry.song_id}: {e}")
            session.rollback()

session.close()