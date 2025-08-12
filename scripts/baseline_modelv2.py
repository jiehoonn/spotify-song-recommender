import numpy as np
from sqlalchemy.orm import sessionmaker
from src.database.models import Song, SongEmotionScore, SongLyricEmbedding
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# --- Setup ---
load_dotenv()
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

AUDIO_FEATURES = [
    'danceability', 'energy', 'valence', 'acousticness',
    'instrumentalness', 'liveness', 'speechiness', 'tempo'
]

emotions = sorted({s.emotion for s in session.query(SongEmotionScore.emotion).distinct()})

audio_feature_values = {f: [] for f in AUDIO_FEATURES}
for song in session.query(Song).all():
    for f in AUDIO_FEATURES:
        val = getattr(song, f, 0.0)
        if val is not None:
            audio_feature_values[f].append(val)

audio_feature_min = {f: min(audio_feature_values[f]) if audio_feature_values[f] else 0.0 for f in AUDIO_FEATURES}
audio_feature_max = {f: max(audio_feature_values[f]) if audio_feature_values[f] else 1.0 for f in AUDIO_FEATURES}

def get_emotion_vector(song_id, emotions):
    scores = {e: 0.0 for e in emotions}
    for score in session.query(SongEmotionScore).filter_by(song_id=song_id):
        scores[score.emotion] = score.score
    return np.array([scores[e] for e in emotions])

def get_audio_vector(song, features):
    vec = []
    for f in features:
        val = getattr(song, f, 0.0) or 0.0
        min_val = audio_feature_min[f]
        max_val = audio_feature_max[f]
        norm_val = (val - min_val) / (max_val - min_val) if max_val > min_val else 0.0
        vec.append(norm_val)
    return np.array(vec)

def get_lyric_embedding(song_id):
    sle = session.query(SongLyricEmbedding).filter_by(song_id=song_id).first()
    if sle and sle.embedding:
        return np.array(sle.embedding)
    return None

def cosine_similarity(a, b):
    if a is None or b is None or np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_popularity(song):
    # Returns normalized popularity or 0.5 if missing
    pop = getattr(song, 'popularity', None)
    return pop / 100.0 if pop is not None else 0.5

def get_tag_counts(song):
    # Returns tag count dict or empty dict
    return getattr(song, 'lastfm_tag_counts', {}) or {}

def weighted_jaccard(tags1, tags2):
    if not tags1 or not tags2:
        return 0.0
    all_tags = set(tags1.keys()) | set(tags2.keys())
    min_sum = sum(min(tags1.get(tag, 0), tags2.get(tag, 0)) for tag in all_tags)
    max_sum = sum(max(tags1.get(tag, 0), tags2.get(tag, 0)) for tag in all_tags)
    return min_sum / max_sum if max_sum > 0 else 0.0

# Weights for each feature type (sum to 1.0)
WEIGHT_LYRICS = 0.42
WEIGHT_AUDIO = 0.25
WEIGHT_EMOTION = 0.17
WEIGHT_POPULARITY = 0.08
WEIGHT_TAGS = 0.08

def load_songs():
    songs = {}
    for song in session.query(Song).all():
        emotion_vec = get_emotion_vector(song.id, emotions)
        audio_vec = get_audio_vector(song, AUDIO_FEATURES)
        lyric_vec = get_lyric_embedding(song.id)
        pop_norm = get_popularity(song)
        tag_counts = get_tag_counts(song)
        songs[song.id] = {
            'title': song.spotify_title,
            'artist': song.spotify_artist,
            'audio_vec': audio_vec,
            'emotion_vec': emotion_vec,
            'lyric_vec': lyric_vec,
            'popularity_norm': pop_norm,
            'tag_counts': tag_counts
        }
    print(f"Loaded {len(songs)} songs from the database.")
    return songs

def hybrid_similarity(song1, song2):
    sim_lyrics = cosine_similarity(song1['lyric_vec'], song2['lyric_vec'])
    sim_audio = cosine_similarity(song1['audio_vec'], song2['audio_vec'])
    sim_emotion = cosine_similarity(song1['emotion_vec'], song2['emotion_vec'])
    sim_popularity = 1.0 - abs(song1['popularity_norm'] - song2['popularity_norm'])
    sim_tags = weighted_jaccard(song1['tag_counts'], song2['tag_counts'])

    # Weighted sum, skip features if missing
    total_weight = 0
    sim_total = 0
    if song1['lyric_vec'] is not None and song2['lyric_vec'] is not None:
        sim_total += WEIGHT_LYRICS * sim_lyrics
        total_weight += WEIGHT_LYRICS
    if song1['audio_vec'] is not None and song2['audio_vec'] is not None:
        sim_total += WEIGHT_AUDIO * sim_audio
        total_weight += WEIGHT_AUDIO
    if song1['emotion_vec'] is not None and song2['emotion_vec'] is not None:
        sim_total += WEIGHT_EMOTION * sim_emotion
        total_weight += WEIGHT_EMOTION
    # Add popularity and tags with their weights
    sim_total += WEIGHT_POPULARITY * sim_popularity
    total_weight += WEIGHT_POPULARITY
    sim_total += WEIGHT_TAGS * sim_tags
    total_weight += WEIGHT_TAGS
    return sim_total / total_weight if total_weight > 0 else 0.0

def browse_songs(songs, page_size=10):
    song_list = [(info['title'], info['artist']) for info in songs.values()]
    total = len(song_list)
    if total == 0:
        print("No songs available in the database.")
        return
    page = 0
    while True:
        start = page * page_size
        end = min(start + page_size, total)
        print(f"\nSongs {start+1}-{end} of {total}:")
        for i, (title, artist) in enumerate(song_list[start:end], start+1):
            print(f"{i}. \"{title}\" by {artist}")
        if end == total:
            print("\nEnd of song list.")
            break
        cmd = input("\nType 'n' for next page, 'q' to quit browsing: ").strip().lower()
        if cmd == 'n':
            page += 1
        else:
            break

def main():
    songs = load_songs()
    print("Welcome to the Hybrid Song Recommender!")
    while True:
        try:
            print("\nOptions:")
            print("1. Find similar songs")
            print("2. Browse available songs")
            print("3. Exit")
            choice = input("Select an option (1/2/3): ").strip()
            if choice == '3':
                break
            elif choice == '2':
                browse_songs(songs)
                continue
            elif choice == '1':
                user_input = input("Enter a song title: ").strip()
                if not user_input:
                    print("Please enter a valid song title.")
                    continue
                found = None
                for song_id, info in songs.items():
                    if info['title'] and info['title'].lower() == user_input.lower():
                        found = (song_id, info)
                        break
                if not found:
                    print("Song not found. Please try again or browse available songs.")
                    continue
                song_id, info = found
                print(f"\nTop 5 similar songs to \"{info['title']}\" by {info['artist']}:")
                similarities = []
                for other_id, other_info in songs.items():
                    if other_id == song_id:
                        continue
                    sim = hybrid_similarity(info, other_info)
                    similarities.append((sim, other_info['title'], other_info['artist']))
                similarities.sort(reverse=True)
                for i, (sim, title, artist) in enumerate(similarities[:5], 1):
                    print(f"{i}. \"{title}\" by {artist} (hybrid similarity: {sim:.2f})")
                print()
            else:
                print("Invalid option. Please try again.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        main()
    finally:
        session.close()