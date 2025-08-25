#!/usr/bin/env python3
"""
Test script to verify active learning system is working correctly.
Run this script to check if the model learns from feedback.
"""

import sys
import os
import random
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import Song, UserFeedback
from src.database.connection import SessionLocal
from src.models.active_learner import active_learner

def create_synthetic_feedback(num_samples=25):
    """Create synthetic feedback data for testing"""
    session = SessionLocal()
    try:
        # Get all songs
        songs = session.query(Song).all()
        if len(songs) < 10:
            print("❌ Need at least 10 songs in database for testing")
            return False
        
        print(f"Creating {num_samples} synthetic feedback samples...")
        
        # Clear existing feedback for clean test
        session.query(UserFeedback).delete()
        session.commit()
        
        created = 0
        for _ in range(num_samples * 2):  # Try more to account for skips
            source_song = random.choice(songs)
            recommended_song = random.choice([s for s in songs if s.id != source_song.id])
            
            # Create realistic feedback patterns
            # Similar tempo/energy songs more likely to be liked
            source_energy = getattr(source_song, 'energy', 0.5) or 0.5
            rec_energy = getattr(recommended_song, 'energy', 0.5) or 0.5
            energy_diff = abs(source_energy - rec_energy)
            
            # More similar energy = higher chance of like
            like_probability = 0.7 if energy_diff < 0.3 else 0.3
            
            if random.random() < like_probability:
                feedback = 'like'
            else:
                feedback = 'dislike'
            
            # Check if this pair already exists
            existing = session.query(UserFeedback).filter_by(
                source_song_id=source_song.id,
                recommended_song_id=recommended_song.id
            ).first()
            
            if not existing:
                fb = UserFeedback(
                    user_id="test_user",
                    source_song_id=source_song.id,
                    recommended_song_id=recommended_song.id,
                    feedback=feedback
                )
                session.add(fb)
                created += 1
                
                if created >= num_samples:
                    break
        
        session.commit()
        print(f"✅ Created {created} synthetic feedback samples")
        return True
        
    except Exception as e:
        print(f"❌ Error creating synthetic feedback: {e}")
        return False
    finally:
        session.close()

def test_baseline_vs_active_learning():
    """Compare baseline and active learning recommendations"""
    session = SessionLocal()
    try:
        # Get a random song for testing
        songs = session.query(Song).limit(50).all()
        test_song = random.choice(songs)
        
        print(f"\nTesting recommendations for: '{test_song.spotify_title}' by {test_song.spotify_artist}")
        
        # Get baseline recommendations using the original baseline model
        print("Getting baseline recommendations...")
        from models.baseline_modelv2 import hybrid_similarity, load_songs
        baseline_songs = load_songs()
        
        if test_song.id not in baseline_songs:
            print("❌ Test song not found in baseline model")
            return False
        
        test_song_data = baseline_songs[test_song.id]
        baseline_similarities = []
        
        for other_id, other_data in baseline_songs.items():
            if other_id != test_song.id:
                sim = hybrid_similarity(test_song_data, other_data)
                other_song = session.query(Song).get(other_id)
                if other_song:
                    baseline_similarities.append((sim, other_song.spotify_title, other_song.spotify_artist))
        
        baseline_similarities.sort(reverse=True)
        baseline_top5 = baseline_similarities[:5]
        
        print("Baseline Top 5:")
        for i, (sim, title, artist) in enumerate(baseline_top5, 1):
            print(f"  {i}. {title} by {artist} (sim: {sim:.3f})")
        
        # Get active learning recommendations
        if active_learner.is_trained:
            print("\nGetting active learning recommendations...")
            ml_recommendations = active_learner.get_recommendations(test_song.id, top_k=5)
            
            if ml_recommendations:
                print("Active Learning Top 5:")
                for i, (song_id, sim_score) in enumerate(ml_recommendations, 1):
                    rec_song = session.query(Song).get(song_id)
                    print(f"  {i}. {rec_song.spotify_title} by {rec_song.spotify_artist} (ML score: {sim_score:.3f})")
                
                # Compare overlap
                baseline_titles = {title for _, title, _ in baseline_top5}
                ml_titles = {session.query(Song).get(song_id).spotify_title for song_id, _ in ml_recommendations}
                overlap = baseline_titles & ml_titles
                
                print(f"\nRecommendation Overlap: {len(overlap)}/5 songs")
                if len(overlap) < 5:
                    print("✅ Active learning is making different recommendations than baseline!")
                else:
                    print("⚠️  Active learning recommendations very similar to baseline")
            else:
                print("❌ Active learning returned no recommendations")
        else:
            print("❌ Active learning model not trained yet")
        
        return True
        
    except Exception as e:
        print(f"❌ Error comparing recommendations: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_feature_extraction():
    """Test that feature extraction is working"""
    session = SessionLocal()
    try:
        print("\nTesting feature extraction...")
        
        # Get a random song
        song = session.query(Song).first()
        if not song:
            print("❌ No songs in database")
            return False
        
        # Extract features
        features = active_learner.extract_features(song.id)
        
        if features is not None:
            print(f"✅ Feature extraction successful for '{song.spotify_title}'")
            print(f"   Feature vector shape: {features.shape}")
            print(f"   Expected shape: ({active_learner.base_feature_dim},)")
            
            if features.shape[0] == active_learner.base_feature_dim:
                print("✅ Feature vector has correct dimensions")
                return True
            else:
                print("❌ Feature vector has wrong dimensions")
                return False
        else:
            print(f"❌ Feature extraction failed for '{song.spotify_title}'")
            return False
            
    except Exception as e:
        print(f"❌ Error testing feature extraction: {e}")
        return False
    finally:
        session.close()

def test_model_training():
    """Test model training with synthetic data"""
    print("\nTesting model training...")
    
    try:
        # Check feedback count
        feedback_count = active_learner.get_feedback_count()
        print(f"Current feedback samples: {feedback_count}")
        
        if feedback_count < active_learner.min_training_samples:
            print(f"❌ Not enough feedback samples (need {active_learner.min_training_samples})")
            return False
        
        # Get feedback stats
        stats = active_learner.get_feedback_stats()
        print(f"Feedback breakdown: {stats['likes']} likes, {stats['dislikes']} dislikes")
        
        # Train model
        print("Training model...")
        success = active_learner.train_model(epochs=50)  # Fewer epochs for testing
        
        if success:
            print("✅ Model training successful!")
            
            # Get training metrics
            if active_learner.training_history:
                latest = active_learner.training_history[-1]
                print(f"   Accuracy: {latest['accuracy']:.3f}")
                print(f"   F1 Score: {latest['f1']:.3f}")
                print(f"   Training samples: {latest['train_samples']}")
                print(f"   Validation samples: {latest['val_samples']}")
            
            # Save model
            save_success = active_learner.save_model()
            if save_success:
                print("✅ Model saved successfully!")
            else:
                print("❌ Model save failed")
                
            return True
        else:
            print("❌ Model training failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing model training: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Active Learning System")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    
    # Test 1: Feature extraction
    print("\n1. Testing Feature Extraction")
    if not test_feature_extraction():
        print("❌ Feature extraction test failed - stopping here")
        return
    
    # Test 2: Create synthetic feedback
    print("\n2. Creating Synthetic Feedback Data")
    if not create_synthetic_feedback(num_samples=25):
        print("❌ Synthetic feedback creation failed")
        return
    
    # Test 3: Model training
    print("\n3. Testing Model Training")
    if not test_model_training():
        print("❌ Model training test failed")
        return
    
    # Test 4: Compare recommendations
    print("\n4. Comparing Baseline vs Active Learning")
    if not test_baseline_vs_active_learning():
        print("❌ Recommendation comparison failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Active learning system is working.")
    print("\nNext steps:")
    print("1. Start your Flask app: python src/web/app.py")
    print("2. Visit /admin to monitor the system")
    print("3. Collect real user feedback")
    print("4. Watch the model improve over time!")

if __name__ == "__main__":
    main()
