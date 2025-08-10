# 1. Load the NRC lexicon
def load_nrc_lexicon(filepath):
    lexicon = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word, emotion, intensity = line.strip().split('\t')
            if word not in lexicon:
                lexicon[word] = {}
            lexicon[word][emotion] = float(intensity)
    return lexicon

# 2. Score lyrics and populate the table
from sqlalchemy.orm import sessionmaker
from src.database.models import Song, Lyrics, SongEmotionScore
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import re
from collections import defaultdict

load_dotenv()
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

lexicon = load_nrc_lexicon('data/NRC-Emotion-Intensity-Lexicon-v1.txt')

for lyrics_entry in session.query(Lyrics).all():
    if not lyrics_entry.cleaned_lyrics:
        continue
    try:
        # Tokenize
        words = re.findall(r"\b[a-zA-Z0-9']+\b", lyrics_entry.cleaned_lyrics.lower())
        emotion_scores = defaultdict(float)
        for word in words:
            if word in lexicon:
                for emotion, intensity in lexicon[word].items():
                    emotion_scores[emotion] += intensity
        # Insert scores
        total_words = len(words)
        for emotion, score in emotion_scores.items():
            normalized_score = score / total_words if total_words else 0.0
            ses = SongEmotionScore(song_id=lyrics_entry.song_id, emotion=emotion, score=normalized_score)
            session.add(ses)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error processing song_id {lyrics_entry.song_id}: {e}")

session.close()