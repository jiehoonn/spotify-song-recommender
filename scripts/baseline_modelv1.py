import numpy as np
from sqlalchemy.orm import sessionmaker
from src.database.models import Song, SongEmotionScore
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

songs = {}
for song in session.query(Song).all():
    emotion_vec = get_emotion_vector(song.id, emotions)
    audio_vec = get_audio_vector(song, AUDIO_FEATURES)
    full_vec = np.concatenate([emotion_vec, audio_vec])
    songs[song.id] = {
        'title': song.spotify_title,
        'artist': song.spotify_artist,
        'vector': full_vec
    }

def cosine_similarity(a, b):
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

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

def print_feature_vectors(song1, song2, emotions, audio_features):
    print("\n--- Feature Comparison ---")
    print(f"Song 1: \"{song1['title']}\" by {song1['artist']}")
    print(f"Song 2: \"{song2['title']}\" by {song2['artist']}")
    print("\nEmotion Scores:")
    for i, e in enumerate(emotions):
        print(f"  {e}: {song1['vector'][i]:.4f} vs {song2['vector'][i]:.4f}")
    print("\nAudio Features (normalized):")
    offset = len(emotions)
    for i, f in enumerate(audio_features):
        print(f"  {f}: {song1['vector'][offset+i]:.4f} vs {song2['vector'][offset+i]:.4f}")
    print("--------------------------\n")

print("Welcome to the Song Recommender!")
while True:
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
        found = None
        for song_id, info in songs.items():
            if info['title'].lower() == user_input.lower():
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
            sim = cosine_similarity(info['vector'], other_info['vector'])
            similarities.append((sim, other_info['title'], other_info['artist'], other_info))
        similarities.sort(reverse=True)
        # Only print feature vectors for the top 5
        for i, (sim, title, artist, other_info) in enumerate(similarities[:5], 1):
            print_feature_vectors(info, other_info, emotions, AUDIO_FEATURES)
            print(f"{i}. \"{title}\" by {artist} (similarity: {sim:.2f})\n")
        print()
    else:
        print("Invalid option. Please try again.")

session.close()