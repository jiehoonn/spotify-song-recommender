import torch
import torch.nn as nn
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import joblib
import os
from typing import Tuple, List, Dict, Optional
import sys
import pandas as pd

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.models import UserFeedback, Song, SongEmotionScore, SongLyricEmbedding
from src.database.connection import SessionLocal

class SiameseNetwork(nn.Module):
    """Neural network that learns song similarity from user feedback"""
    
    def __init__(self, input_dim: int):
        super().__init__()
        # Input will be [song1_features + song2_features + abs_diff] = input_dim * 3
        self.network = nn.Sequential(
            nn.Linear(input_dim * 3, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.3),
            
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.3),
            
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(128, 64),
            nn.ReLU(),
            
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, song1_features: torch.Tensor, song2_features: torch.Tensor) -> torch.Tensor:
        # Create pairwise features: [song1, song2, |song1-song2|]
        abs_diff = torch.abs(song1_features - song2_features)
        combined = torch.cat([song1_features, song2_features, abs_diff], dim=1)
        return self.network(combined)

class ActiveLearningRecommender:
    def __init__(self):
        self.base_feature_dim = 785  # 768 (embeddings) + 8 (audio) + 8 (emotions) + 1 (popularity)
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.min_training_samples = 15
        self.training_history = []
        
    def extract_features(self, song_id: int) -> Optional[np.ndarray]:
        """Extract concatenated feature vector for a song"""
        session = SessionLocal()
        try:
            # Import here to avoid circular imports
            from models.baseline_modelv2 import (
                get_lyric_embedding, get_audio_vector, get_emotion_vector, 
                get_popularity, emotions, AUDIO_FEATURES, 
                audio_feature_min, audio_feature_max
            )
            
            song = session.query(Song).get(song_id)
            if not song:
                return None
                
            # Get all feature components
            lyric_vec = get_lyric_embedding(song_id)
            if lyric_vec is None:
                lyric_vec = np.zeros(768)
                
            audio_vec = get_audio_vector(song, AUDIO_FEATURES)
            emotion_vec = get_emotion_vector(song_id, emotions)
            popularity = get_popularity(song)
            
            # Concatenate all features
            features = np.concatenate([
                lyric_vec,
                audio_vec, 
                emotion_vec,
                [popularity]
            ])
            return features
        except Exception as e:
            print(f"Error extracting features for song {song_id}: {e}")
            return None
        finally:
            session.close()
    
    def get_feedback_count(self) -> int:
        """Check how many feedback samples we have"""
        session = SessionLocal()
        try:
            return session.query(UserFeedback).count()
        finally:
            session.close()
    
    def get_feedback_stats(self) -> Dict:
        """Get detailed feedback statistics"""
        session = SessionLocal()
        try:
            total = session.query(UserFeedback).count()
            likes = session.query(UserFeedback).filter_by(feedback='like').count()
            dislikes = session.query(UserFeedback).filter_by(feedback='dislike').count()
            skips = session.query(UserFeedback).filter_by(feedback='skip').count()
            
            return {
                'total': total,
                'likes': likes,
                'dislikes': dislikes,
                'skips': skips,
                'like_ratio': likes / total if total > 0 else 0
            }
        finally:
            session.close()
    
    def create_training_data(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Create training pairs from user feedback"""
        session = SessionLocal()
        try:
            feedback_data = session.query(UserFeedback).all()
            
            if len(feedback_data) < self.min_training_samples:
                print(f"Need at least {self.min_training_samples} feedback samples, have {len(feedback_data)}")
                return None, None
            
            X_pairs = []
            y_labels = []
            
            print(f"Processing {len(feedback_data)} feedback samples...")
            
            processed = 0
            for fb in feedback_data:
                song1_features = self.extract_features(fb.source_song_id)
                song2_features = self.extract_features(fb.recommended_song_id)
                
                if song1_features is not None and song2_features is not None:
                    # Convert feedback to binary labels
                    if fb.feedback == 'like':
                        label = 1
                    elif fb.feedback == 'dislike':
                        label = 0
                    else:  # skip
                        continue  # Ignore skip for now
                    
                    X_pairs.append(np.concatenate([song1_features, song2_features]))
                    y_labels.append(label)
                    processed += 1
            
            if len(X_pairs) < self.min_training_samples:
                print(f"After processing, only {len(X_pairs)} valid samples")
                return None, None
            
            print(f"Created {len(X_pairs)} training pairs from {processed} feedback samples")
            return np.array(X_pairs), np.array(y_labels)
            
        except Exception as e:
            print(f"Error creating training data: {e}")
            return None, None
        finally:
            session.close()
    
    def train_model(self, epochs: int = 100) -> bool:
        """Train the neural network on user feedback"""
        X, y = self.create_training_data()
        
        if X is None or y is None:
            return False
        
        try:
            print("Training active learning model...")
            print(f"Dataset: {len(X)} samples, {sum(y)} likes, {len(y) - sum(y)} dislikes")
            
            # Standardize features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            test_size = min(0.3, max(0.1, 20 / len(X)))  # Adaptive test size
            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=test_size, random_state=42, 
                stratify=y if len(np.unique(y)) > 1 else None
            )
            
            print(f"Train: {len(X_train)}, Validation: {len(X_val)}")
            
            # Create model
            input_dim = self.base_feature_dim
            self.model = SiameseNetwork(input_dim)
            
            # Training setup
            criterion = nn.BCELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)
            
            # Convert to tensors and split back into song pairs
            mid_point = X_train.shape[1] // 2
            X_train_song1 = torch.FloatTensor(X_train[:, :mid_point])
            X_train_song2 = torch.FloatTensor(X_train[:, mid_point:])
            y_train_tensor = torch.FloatTensor(y_train).unsqueeze(1)
            
            X_val_song1 = torch.FloatTensor(X_val[:, :mid_point])
            X_val_song2 = torch.FloatTensor(X_val[:, mid_point:])
            y_val_tensor = torch.FloatTensor(y_val).unsqueeze(1)
            
            # Training loop with early stopping
            best_val_loss = float('inf')
            patience_counter = 0
            training_losses = []
            validation_losses = []
            
            self.model.train()
            for epoch in range(epochs):
                # Training
                optimizer.zero_grad()
                outputs = self.model(X_train_song1, X_train_song2)
                train_loss = criterion(outputs, y_train_tensor)
                train_loss.backward()
                optimizer.step()
                
                # Validation
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(X_val_song1, X_val_song2)
                    val_loss = criterion(val_outputs, y_val_tensor)
                    
                scheduler.step(val_loss)
                
                training_losses.append(train_loss.item())
                validation_losses.append(val_loss.item())
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if epoch % 20 == 0 or patience_counter >= 15:
                    val_preds = (val_outputs > 0.5).float()
                    accuracy = (val_preds.squeeze() == y_val_tensor.squeeze()).float().mean()
                    print(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {accuracy:.4f}")
                
                if patience_counter >= 15:
                    print("Early stopping triggered")
                    break
                
                self.model.train()
            
            # Final validation metrics
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_song1, X_val_song2)
                val_preds = (val_outputs > 0.5).float().squeeze()
                accuracy = (val_preds == y_val_tensor.squeeze()).float().mean()
                
                # Calculate precision, recall, F1
                y_val_np = y_val_tensor.squeeze().numpy()
                val_preds_np = val_preds.numpy()
                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_val_np, val_preds_np, average='binary', zero_division=0
                )
            
            print(f"Final Metrics - Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
            
            # Store training history
            self.training_history.append({
                'accuracy': accuracy.item(),
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'train_samples': len(X_train),
                'val_samples': len(X_val),
                'epochs_trained': epoch + 1
            })
            
            self.is_trained = True
            return True
            
        except Exception as e:
            print(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict_similarity(self, song1_id: int, song2_id: int) -> Optional[float]:
        """Predict similarity between two songs"""
        if not self.is_trained or self.model is None:
            return None
        
        try:
            features1 = self.extract_features(song1_id)
            features2 = self.extract_features(song2_id)
            
            if features1 is None or features2 is None:
                return None
            
            # Prepare input
            combined_features = np.concatenate([features1, features2]).reshape(1, -1)
            scaled_features = self.scaler.transform(combined_features)
            
            # Split for model input
            mid_point = scaled_features.shape[1] // 2
            song1_tensor = torch.FloatTensor(scaled_features[:, :mid_point])
            song2_tensor = torch.FloatTensor(scaled_features[:, mid_point:])
            
            self.model.eval()
            with torch.no_grad():
                similarity = self.model(song1_tensor, song2_tensor).item()
            
            return similarity
        except Exception as e:
            print(f"Error predicting similarity: {e}")
            return None
    
    def get_recommendations(self, song_id: int, top_k: int = 5) -> List[Tuple[int, float]]:
        """Get recommendations using learned model"""
        if not self.is_trained:
            return []
        
        session = SessionLocal()
        try:
            all_songs = session.query(Song).filter(Song.id != song_id).all()
            
            similarities = []
            for other_song in all_songs:
                sim_score = self.predict_similarity(song_id, other_song.id)
                if sim_score is not None:
                    similarities.append((other_song.id, sim_score))
            
            if not similarities:
                return []
            
            # Sort by similarity and return top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
        finally:
            session.close()
    
    def analyze_feature_importance(self, song1_id: int, song2_id: int) -> Dict:
        """Analyze which features contribute most to similarity prediction"""
        features1 = self.extract_features(song1_id)
        features2 = self.extract_features(song2_id)
        
        if features1 is None or features2 is None:
            return {}
        
        # Calculate component similarities
        lyric_sim = np.dot(features1[:768], features2[:768]) / (
            np.linalg.norm(features1[:768]) * np.linalg.norm(features2[:768]) + 1e-8
        )
        audio_sim = np.dot(features1[768:776], features2[768:776]) / (
            np.linalg.norm(features1[768:776]) * np.linalg.norm(features2[768:776]) + 1e-8
        )
        emotion_sim = np.dot(features1[776:786], features2[776:786]) / (
            np.linalg.norm(features1[776:786]) * np.linalg.norm(features2[776:786]) + 1e-8
        )
        popularity_diff = abs(features1[786] - features2[786])
        
        ml_similarity = self.predict_similarity(song1_id, song2_id) or 0
        
        return {
            'ml_similarity': ml_similarity,
            'lyric_similarity': lyric_sim,
            'audio_similarity': audio_sim,
            'emotion_similarity': emotion_sim,
            'popularity_difference': popularity_diff,
            'features_extracted': True
        }
    
    def save_model(self, path: str = "models/active_learner.pkl"):
        """Save trained model and scaler"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            state = {
                'model_state_dict': self.model.state_dict() if self.model else None,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'base_feature_dim': self.base_feature_dim,
                'training_history': self.training_history,
                'min_training_samples': self.min_training_samples
            }
            joblib.dump(state, path)
            print(f"Model saved to {path}")
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, path: str = "models/active_learner.pkl"):
        """Load trained model and scaler"""
        try:
            if not os.path.exists(path):
                print("No saved model found. Will use baseline until trained.")
                return False
                
            state = joblib.load(path)
            
            if state.get('model_state_dict'):
                input_dim = state['base_feature_dim']
                self.model = SiameseNetwork(input_dim)
                self.model.load_state_dict(state['model_state_dict'])
                self.model.eval()
            
            self.scaler = state.get('scaler')
            self.is_trained = state.get('is_trained', False)
            self.base_feature_dim = state.get('base_feature_dim', self.base_feature_dim)
            self.training_history = state.get('training_history', [])
            self.min_training_samples = state.get('min_training_samples', 15)
            
            print(f"Model loaded from {path}. Trained: {self.is_trained}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

# Global instance
active_learner = ActiveLearningRecommender()
