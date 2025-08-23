from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, ARRAY, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
import datetime

Base = declarative_base()

class Song(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key=True)
    lastfm_mbid = Column(String(64))
    lastfm_title = Column(String(255))
    lastfm_artist = Column(String(255))
    lastfm_url = Column(String)
    lastfm_playcount = Column(Integer)
    lastfm_listeners = Column(Integer)
    spotify_id = Column(String(64), unique=True)
    spotify_title = Column(String(255))
    spotify_artist = Column(String(255))
    spotify_album = Column(String(255))
    spotify_popularity = Column(Integer)
    spotify_duration_ms = Column(Integer)
    spotify_url = Column(String)
    reccobeats_id = Column(String(64))
    acousticness = Column(Float)
    danceability = Column(Float)
    energy = Column(Float)
    instrumentalness = Column(Float)
    liveness = Column(Float)
    loudness = Column(Float)
    speechiness = Column(Float)
    tempo = Column(Float)
    valence = Column(Float)
    popularity = Column(Integer)
    lastfm_tag_counts = Column(JSONB)
    lyric_embedding = relationship("SongLyricEmbedding", uselist=False, back_populates="song")
    lyrics = relationship("Lyrics", uselist=False, back_populates="song")
    emotion_scores = relationship("SongEmotionScore", back_populates="song", cascade="all, delete-orphan")

class Lyrics(Base):
    __tablename__ = 'lyrics'
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.id'), unique=True)
    cleaned_lyrics = Column(Text)
    song = relationship("Song", back_populates="lyrics")

class SongEmotionScore(Base):
    __tablename__ = 'song_emotion_scores'
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.id', ondelete='CASCADE'))
    emotion = Column(String(32))
    score = Column(Float)
    song = relationship("Song", back_populates="emotion_scores")
    total_words = Column(Integer)
    matched_words = Column(Integer)
    __table_args__ = (UniqueConstraint('song_id', 'emotion', name='uix_song_emotion'),)
    
class SongLyricEmbedding(Base):
    __tablename__ = 'song_lyric_embeddings'
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.id', ondelete='CASCADE'), unique=True, nullable=False)
    embedding = Column(ARRAY(Float))  # Stores the vector as a float array
    model_name = Column(String(128))  # e.g., 'all-mpnet-base-v2'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    song = relationship("Song", back_populates="lyric_embedding")

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=True)  # Optional for future multi-user support
    source_song_id = Column(Integer, ForeignKey("songs.id", ondelete="CASCADE"))
    recommended_song_id = Column(Integer, ForeignKey("songs.id", ondelete="CASCADE"))
    feedback = Column(String)  # e.g., "like", "dislike", "skip", or rating
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)