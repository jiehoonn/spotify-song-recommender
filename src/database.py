from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from config.settings import settings

Base = declarative_base()

class Track(Base):
    __tablename__ = 'tracks'
    
    id = Column(String, primary_key=True)  # Spotify track ID
    name = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String)
    popularity = Column(Integer)
    
    # Audio features
    danceability = Column(Float)
    energy = Column(Float)
    valence = Column(Float)
    tempo = Column(Float)
    key = Column(Integer)
    mode = Column(Integer)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserFeedback(Base):
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    track_id = Column(String, ForeignKey('tracks.id'))
    feedback_type = Column(String)  # 'like', 'skip', 'save'
    context = Column(String)  # playlist context
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    track = relationship("Track")

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

# Only create tables if this file is run directly
if __name__ == "__main__":
    init_database()