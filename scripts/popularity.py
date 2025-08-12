import requests
import time
from sqlalchemy.orm import sessionmaker
from src.database.models import Song
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import base64

load_dotenv()
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

def get_spotify_access_token(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    resp = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    if resp.status_code != 200:
        raise Exception(f"Failed to authenticate with Spotify API: {resp.text}")
    return resp.json()['access_token']

SPOTIFY_ACCESS_TOKEN = get_spotify_access_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

headers = {
    "Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"
}

updated = 0
for song in session.query(Song).all():
    if song.spotify_id:
        url = f"https://api.spotify.com/v1/tracks/{song.spotify_id}"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                popularity = data.get('popularity')
                if popularity is not None:
                    song.popularity = popularity
                    updated += 1
            else:
                print(f"Failed to fetch {song.spotify_id}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Error fetching {song.spotify_id}: {e}")
        time.sleep(0.1)  # Be nice to the API, avoid rate limits

session.commit()
print(f"Updated popularity for {updated} songs using Spotify API.")
session.close()