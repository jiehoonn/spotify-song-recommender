from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

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
    lyrics = relationship("Lyrics", uselist=False, back_populates="song")

class Lyrics(Base):
    __tablename__ = 'lyrics'
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.id'), unique=True)
    cleaned_lyrics = Column(Text)
    song = relationship("Song", back_populates="lyrics")