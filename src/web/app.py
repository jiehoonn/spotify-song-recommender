from flask import Flask, render_template, request, redirect, url_for, jsonify
from src.database.connection import SessionLocal
from src.database.models import Song, UserFeedback, SongEmotionScore, SongLyricEmbedding
import numpy as np
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Import active learner and scheduler
try:
    from src.models.active_learner import active_learner
    from src.models.scheduler import model_scheduler
    
    # Load existing model if available
    active_learner.load_model()
    print(f"Active learner loaded. Trained: {active_learner.is_trained}")
    
    # Start background scheduler for automatic retraining
    model_scheduler.start_scheduler()
    print("Background scheduler started")
    
except ImportError as e:
    print(f"Active learner not available: {e}, using baseline only")
    active_learner = None
    model_scheduler = None

AUDIO_FEATURES = [
    'danceability', 'energy', 'valence', 'acousticness',
    'instrumentalness', 'liveness', 'speechiness', 'tempo'
]
WEIGHT_LYRICS = 0.42
WEIGHT_AUDIO = 0.25
WEIGHT_EMOTION = 0.17
WEIGHT_POPULARITY = 0.08
WEIGHT_TAGS = 0.08

def get_emotion_vector(session, song_id, emotions):
    scores = {e: 0.0 for e in emotions}
    for score in session.query(SongEmotionScore).filter_by(song_id=song_id):
        scores[score.emotion] = score.score
    return np.array([scores[e] for e in emotions])

def get_audio_vector(song, features, audio_feature_min, audio_feature_max):
    vec = []
    for f in features:
        val = getattr(song, f, 0.0) or 0.0
        min_val = audio_feature_min[f]
        max_val = audio_feature_max[f]
        norm_val = (val - min_val) / (max_val - min_val) if max_val > min_val else 0.0
        vec.append(norm_val)
    return np.array(vec)

def get_lyric_embedding(session, song_id):
    sle = session.query(SongLyricEmbedding).filter_by(song_id=song_id).first()
    if sle and sle.embedding:
        return np.array(sle.embedding)
    return None

def cosine_similarity(a, b):
    if a is None or b is None or np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_popularity(song):
    pop = getattr(song, 'popularity', None)
    return pop / 100.0 if pop is not None else 0.5

def get_tag_counts(song):
    return getattr(song, 'lastfm_tag_counts', {}) or {}

def weighted_jaccard(tags1, tags2):
    if not tags1 or not tags2:
        return 0.0
    all_tags = set(tags1.keys()) | set(tags2.keys())
    min_sum = sum(min(tags1.get(tag, 0), tags2.get(tag, 0)) for tag in all_tags)
    max_sum = sum(max(tags1.get(tag, 0), tags2.get(tag, 0)) for tag in all_tags)
    return min_sum / max_sum if max_sum > 0 else 0.0

def hybrid_similarity(song1, song2):
    sim_lyrics = cosine_similarity(song1['lyric_vec'], song2['lyric_vec'])
    sim_audio = cosine_similarity(song1['audio_vec'], song2['audio_vec'])
    sim_emotion = cosine_similarity(song1['emotion_vec'], song2['emotion_vec'])
    sim_popularity = 1.0 - abs(song1['popularity_norm'] - song2['popularity_norm'])
    sim_tags = weighted_jaccard(song1['tag_counts'], song2['tag_counts'])

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
    sim_total += WEIGHT_POPULARITY * sim_popularity
    total_weight += WEIGHT_POPULARITY
    sim_total += WEIGHT_TAGS * sim_tags
    total_weight += WEIGHT_TAGS
    return sim_total / total_weight if total_weight > 0 else 0.0

SONGS_PER_PAGE = 10

@app.route("/", methods=["GET"])
def home():
    session = SessionLocal()
    page = int(request.args.get("page", 1))
    total_songs = session.query(Song).count()
    songs = (
        session.query(Song)
        .order_by(Song.id)
        .offset((page - 1) * SONGS_PER_PAGE)
        .limit(SONGS_PER_PAGE)
        .all()
    )
    session.close()
    return render_template(
        "home.html",
        songs=songs,
        page=page,
        total_songs=total_songs,
        songs_per_page=SONGS_PER_PAGE
    )

@app.route("/recommend/<int:song_id>", methods=["GET", "POST"])
def recommend(song_id):
    session = SessionLocal()
    song = session.query(Song).get(song_id)
    
    # Try active learning first, fallback to baseline
    top5 = []
    used_active_learning = False
    model_info = "Baseline"
    
    if active_learner and active_learner.is_trained:
        try:
            print("Using active learning model...")
            recommendations = active_learner.get_recommendations(song_id, top_k=5)
            if recommendations:  # If we got recommendations
                used_active_learning = True
                model_info = "Active Learning"
                for rec_id, sim_score in recommendations:
                    rec_song = session.query(Song).get(rec_id)
                    if rec_song:
                        top5.append((sim_score, rec_song, rec_song.spotify_title, rec_song.spotify_artist))
        except Exception as e:
            print(f"Active learning failed: {e}")
    
    # Fallback to baseline if active learning failed or isn't available
    if not top5:
        print("Using baseline model...")
        all_songs = session.query(Song).all()
        emotions = sorted({s.emotion for s in session.query(SongEmotionScore.emotion).distinct()})
        audio_feature_values = {f: [] for f in AUDIO_FEATURES}
        for s in all_songs:
            for f in AUDIO_FEATURES:
                val = getattr(s, f, 0.0)
                if val is not None:
                    audio_feature_values[f].append(val)
        audio_feature_min = {f: min(audio_feature_values[f]) if audio_feature_values[f] else 0.0 for f in AUDIO_FEATURES}
        audio_feature_max = {f: max(audio_feature_values[f]) if audio_feature_values[f] else 1.0 for f in AUDIO_FEATURES}

        def build_song_dict(s):
            return {
                'title': s.spotify_title,
                'artist': s.spotify_artist,
                'audio_vec': get_audio_vector(s, AUDIO_FEATURES, audio_feature_min, audio_feature_max),
                'emotion_vec': get_emotion_vector(session, s.id, emotions),
                'lyric_vec': get_lyric_embedding(session, s.id),
                'popularity_norm': get_popularity(s),
                'tag_counts': get_tag_counts(s)
            }
        
        song_dict = build_song_dict(song)
        similarities = []
        for other in all_songs:
            if other.id == song_id:
                continue
            other_dict = build_song_dict(other)
            sim = hybrid_similarity(song_dict, other_dict)
            similarities.append((sim, other, other.spotify_title, other.spotify_artist))
        similarities.sort(reverse=True, key=lambda x: x[0])
        top5 = similarities[:5]

    success = False
    if request.method == "POST":
        rec_id = int(request.form["recommended_song_id"])
        feedback = request.form["feedback"]
        user_id = "anonymous"
        
        # Store feedback
        fb = UserFeedback(
            user_id=user_id,
            source_song_id=song_id,
            recommended_song_id=rec_id,
            feedback=feedback
        )
        session.add(fb)
        session.commit()
        success = True
        
        # Check if we have enough feedback to train for the first time
        if active_learner and not active_learner.is_trained:
            feedback_count = active_learner.get_feedback_count()
            print(f"Total feedback samples: {feedback_count}")
            
            if feedback_count >= active_learner.min_training_samples:
                print("Enough feedback collected! Training model for first time...")
                if active_learner.train_model():
                    active_learner.save_model()
                    print("Model trained and saved!")

    response = render_template("recommend.html", 
                             song=song, 
                             recommendations=top5, 
                             success=success,
                             model_used=model_info)
    session.close()
    return response

@app.route("/admin/retrain", methods=["POST"])
def retrain_model():
    """Manually retrain the model"""
    if not active_learner:
        return jsonify({"status": "error", "message": "Active learner not available"})
    
    feedback_count = active_learner.get_feedback_count()
    if feedback_count < active_learner.min_training_samples:
        return jsonify({
            "status": "error", 
            "message": f"Need at least {active_learner.min_training_samples} feedback samples, have {feedback_count}"
        })
    
    success = active_learner.train_model()
    if success:
        active_learner.save_model()
        latest_metrics = active_learner.training_history[-1] if active_learner.training_history else {}
        return jsonify({
            "status": "success", 
            "message": "Model retrained successfully",
            "metrics": latest_metrics
        })
    else:
        return jsonify({"status": "error", "message": "Training failed"})

@app.route("/admin/stats")
def admin_stats():
    """Show system statistics"""
    session = SessionLocal()
    try:
        total_feedback = session.query(UserFeedback).count()
        likes = session.query(UserFeedback).filter_by(feedback='like').count()
        dislikes = session.query(UserFeedback).filter_by(feedback='dislike').count()
        skips = session.query(UserFeedback).filter_by(feedback='skip').count()
        
        stats = {
            "total_songs": session.query(Song).count(),
            "total_feedback": total_feedback,
            "likes": likes,
            "dislikes": dislikes,
            "skips": skips,
            "like_ratio": likes / total_feedback if total_feedback > 0 else 0,
            "model_trained": active_learner.is_trained if active_learner else False,
            "feedback_needed": max(0, (active_learner.min_training_samples if active_learner else 15) - total_feedback),
            "training_history": active_learner.training_history if active_learner else []
        }
        return jsonify(stats)
    finally:
        session.close()

@app.route("/admin/analyze/<int:song1_id>/<int:song2_id>")
def analyze_similarity(song1_id, song2_id):
    """Analyze similarity between two songs"""
    if not active_learner or not active_learner.is_trained:
        return jsonify({"error": "Active learner not trained"})
    
    analysis = active_learner.analyze_feature_importance(song1_id, song2_id)
    
    # Get song details
    session = SessionLocal()
    try:
        song1 = session.query(Song).get(song1_id)
        song2 = session.query(Song).get(song2_id)
        
        return jsonify({
            "song1": {"title": song1.spotify_title, "artist": song1.spotify_artist},
            "song2": {"title": song2.spotify_title, "artist": song2.spotify_artist},
            "analysis": analysis
        })
    finally:
        session.close()

@app.route("/admin")
def admin_dashboard():
    """Simple admin dashboard"""
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)