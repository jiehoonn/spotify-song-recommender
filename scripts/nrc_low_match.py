from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.database.models import Song, Lyrics, SongEmotionScore
import os
from dotenv import load_dotenv
import string

def load_nrc_lexicon(filepath):
    nrc_words = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word, emotion, intensity = line.strip().split('\t')
            word = word.strip()
            emotion = emotion.strip()
            if word not in nrc_words:
                nrc_words[word] = set()
            nrc_words[word].add(emotion)
    return nrc_words

load_dotenv()
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

NRC_LEXICON_PATH = "data/NRC-Emotion-Intensity-Lexicon-v1.txt"
nrc_words = load_nrc_lexicon(NRC_LEXICON_PATH)
print(f"Loaded {len(nrc_words)} NRC words. Sample: {list(nrc_words)[:10]}")
MIN_MATCHED_WORDS = 10

for lyrics in session.query(Lyrics).all():
    if not lyrics.cleaned_lyrics:
        continue
    words = [w.strip(string.punctuation) for w in lyrics.cleaned_lyrics.lower().split()]
    total = len(words)
    # Build emotion-to-matched-words count
    emotion_word_count = {}
    for w in words:
        if w in nrc_words:
            for emotion in nrc_words[w]:
                emotion_word_count[emotion] = emotion_word_count.get(emotion, 0) + 1
    # Update all emotion scores for this song
    for score in session.query(SongEmotionScore).filter_by(song_id=lyrics.song_id):
        score.total_words = total
        score.matched_words = emotion_word_count.get(score.emotion, 0)
    # Print low coverage for any emotion
    if sum(emotion_word_count.values()) < MIN_MATCHED_WORDS:
        song = session.get(Song, lyrics.song_id)
        print(f"Low NRC coverage: \"{song.spotify_title}\" by {song.spotify_artist} (matched: {sum(emotion_word_count.values())}/{total})")
session.commit()
session.close()