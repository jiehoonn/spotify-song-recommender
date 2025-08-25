#!/usr/bin/env python3
"""
Setup script to create all database tables in production.
Run this once after deployment to set up your database schema.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.models import Base
from src.database.connection import engine
from sqlalchemy import text

def create_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            
        print(f"\nCreated tables: {', '.join(tables)}")
        
        expected_tables = ['songs', 'lyrics', 'song_emotion_scores', 'song_lyric_embeddings', 'user_feedback']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
        else:
            print("✅ All expected tables present!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

def check_connection():
    """Test database connection"""
    try:
        print("Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up production database...")
    print("=" * 50)
    
    if check_connection():
        create_tables()
        print("\n✅ Production database setup complete!")
        print("\nNext steps:")
        print("1. Your Flask app should now work with the production database")
        print("2. Users can provide feedback through the web interface")
        print("3. Visit /admin to monitor the system")
    else:
        print("❌ Setup failed - check your DATABASE_URL environment variable")
