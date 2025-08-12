from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_
from src.database.models import Song, Lyrics, SongEmotionScore
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

print("Checking 'songs' table for NULL or 0 values...")
for song in session.query(Song).filter(
    or_(
        Song.spotify_id == None,
        Song.spotify_title == None,
        Song.spotify_artist == None,
        Song.danceability == None, Song.danceability == 0,
        Song.energy == None, Song.energy == 0,
        Song.valence == None, Song.valence == 0,
        Song.acousticness == None, Song.acousticness == 0,
        Song.instrumentalness == None, Song.instrumentalness == 0,
        Song.liveness == None, Song.liveness == 0,
        Song.loudness == None, Song.loudness == 0,
        Song.speechiness == None, Song.speechiness == 0,
        Song.tempo == None, Song.tempo == 0
    )
).all():
    print(f"Song ID {song.id}: {song.spotify_title} by {song.spotify_artist}")

print("\nChecking 'lyrics' table for NULL or empty cleaned_lyrics...")
for lyrics in session.query(Lyrics).filter(
    or_(Lyrics.cleaned_lyrics == None, Lyrics.cleaned_lyrics == '')
).all():
    print(f"Lyrics ID {lyrics.id}: song_id={lyrics.song_id}")

print("\nChecking 'song_emotion_scores' table for NULL or 0 scores...")
for score in session.query(SongEmotionScore).filter(
    or_(SongEmotionScore.score == None, SongEmotionScore.score == 0)
).all():
    print(f"Score ID {score.id}: song_id={score.song_id}, emotion={score.emotion}")

session.close()