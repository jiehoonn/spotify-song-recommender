import requests
import json
from dotenv import load_dotenv
import os
# import musicbrainzngs

load_dotenv() # Load environment variables from .env.

# Test the ReccoBeats API endpoint
# ReccoBeats API does not offer a way to obtain a list of multiple tracks without knowing the track ID. Need to use another way to just obtain a list of tracks within a genre for now.
# Audio Features Available! 
def test_reccobeats_api():
    """Test the ReccoBeats API endpoint."""
    base_url = os.getenv("RECCOBEATS_API_URL")
    
    print("Testing ReccoBeats API...")
    
    # Headers from documentation
    headers = {
        'Accept': 'application/json'
    }
    
    # Test GET track detail endpoint
    track_id = "878dadea-33c5-4c08-bdb9-e2b117475a99" # Taylor Swift - All Too Well
    track_url = f"{base_url}/track/{track_id}/audio-features"
    
    try:
        response = requests.get(track_url, headers=headers)
        print(f"Track Details - Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Track details retrieved successfully.")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed to retrieve track details.")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error during GET request: {e}")

# Test the Last.fm API endpoint
# Last.fm API requires an API key, which should be set in the environment variables.
# Endpoint URL is quite specific
# Could get top tracks based on charts or location
# Maybe we can use another API to just gather a bunch of songs, and do a join to filter out songs that are only also available on Last.fm AND ReccoBeats
def test_lastfm_api():
    """Test the Last.fm API endpoint."""
    api_key = os.getenv("LASTFM_API_KEY")
    base_url = os.getenv("LASTFM_API_URL")
    
    print("\nTesting Last.fm API...")
    
    # chart.getTopTracks endpoint
    top_tracks_url = f"{base_url}?method=chart.gettoptracks&api_key={api_key}&format=json"
    
    try:
        response = requests.get(top_tracks_url)
        print(f"Top Tracks - Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Top tracks retrieved successfully.")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed to retrieve top tracks.")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error during GET request: {e}")

def test_musicbrainz():
    """Test the MusicBrainz Python Library."""
    # Identify your application
    musicbrainzngs.set_useragent("rnb-song-fetcher", "1.0", "jiehoonn@gmail.com")

    # Search for works tagged as R&B and of type "song"
    result = musicbrainzngs.search_works(type="song", tag="rap", limit=25, offset=0)
    works = result.get("work-list", [])

    # Iterate through the work list and fetch detailed info
    for work in works:
        mbid = work["id"]
        title = work.get("title")
        
        # Valid includes for works are: artist-rels, recording-rels, tags
        # Remove "genres" as it's not valid for works
        try:
            details = musicbrainzngs.get_work_by_id(
                mbid,
                includes=["artist-rels", "recording-rels", "tags"]
            )
            detailed_work = details.get("work", {})
            print(f"Title: {title}")
            print(f"Language: {detailed_work.get('language')}")
            print(f"Artist Relations: {detailed_work.get('artist-relation-list')}")
            print(f"Tags: {detailed_work.get('tag-list')}")
            print("---")
        except Exception as e:
            print(f"Error fetching details for {title}: {e}")


if __name__ == "__main__":
    test_reccobeats_api()
    print("ReccoBeats API tests completed.")
    test_lastfm_api()
    print("Last.fm API tests completed.")
    # test_musicbrainz()
    # print("MusicBrainz API tests completed.")