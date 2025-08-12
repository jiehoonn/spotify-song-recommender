from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import sessionmaker
from src.database.models import Song, Lyrics, SongLyricEmbedding
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

model_name = 'all-mpnet-base-v2'
model = SentenceTransformer(model_name)

for lyrics_entry in session.query(Lyrics).all():
    if not lyrics_entry.cleaned_lyrics:
        continue
    try:
        embedding = model.encode(lyrics_entry.cleaned_lyrics)
        sle = session.query(SongLyricEmbedding).filter_by(song_id=lyrics_entry.song_id).first()
        if sle:
            sle.embedding = embedding.tolist()
            sle.model_name = model_name
        else:
            sle = SongLyricEmbedding(
                song_id=lyrics_entry.song_id,
                embedding=embedding.tolist(),
                model_name=model_name
            )
            session.add(sle)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error processing song_id {lyrics_entry.song_id}: {e}")

session.close()