from sqlalchemy.orm import sessionmaker
from src.database.models import Lyrics
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

languages = {}
for entry in session.query(Lyrics).all():
    if entry.cleaned_lyrics:
        try:
            lang = detect(entry.cleaned_lyrics)
            languages[lang] = languages.get(lang, 0) + 1
        except Exception:
            pass

print("Languages detected in lyrics table:")
for lang, count in languages.items():
    print(f"{lang}: {count}")

session.close()