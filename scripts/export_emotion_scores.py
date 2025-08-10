import csv
from sqlalchemy.orm import sessionmaker
from src.database.models import Song, SongEmotionScore
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

with open('emotion_scores_export.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['song_id', 'spotify_title', 'spotify_artist', 'emotion', 'score'])
    for score in session.query(SongEmotionScore).join(Song, SongEmotionScore.song_id == Song.id):
        writer.writerow([
            score.song_id,
            score.song.spotify_title,
            score.song.spotify_artist,
            score.emotion,
            score.score
        ])

session.close()
print("Exported to emotion_scores_export.csv")