import requests
from sqlalchemy.orm import sessionmaker
from src.database.models import Song
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import time

load_dotenv()
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def get_lastfm_top_tags(song):
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "track.getTopTags",
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }
    if song.lastfm_mbid:
        params["mbid"] = song.lastfm_mbid
    else:
        params["artist"] = song.lastfm_artist
        params["track"] = song.lastfm_title
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        tags = []
        tag_counts = {}
        if 'toptags' in data and 'tag' in data['toptags']:
            for t in data['toptags']['tag']:
                if 'name' in t and 'count' in t:
                    tags.append(t['name'])
                    tag_counts[t['name']] = int(t['count'])
        return tags, tag_counts
    except Exception as e:
        print(f"Error fetching tags for {song.lastfm_artist} - {song.lastfm_title}: {e}")
        return [], {}

updated = 0
for song in session.query(Song).all():
    tags, tag_counts = get_lastfm_top_tags(song)
    if tags:
        song.lastfm_tags = tags
        song.lastfm_tag_counts = tag_counts
        updated += 1
    else:
        print(f"No tags for: {song.lastfm_artist} - {song.lastfm_title} (mbid: {song.lastfm_mbid})")
    time.sleep(0.2)
session.commit()
print(f"Updated Last.fm tags for {updated} songs.")
session.close()