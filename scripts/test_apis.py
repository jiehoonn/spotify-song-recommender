import requests
import json
from dotenv import load_dotenv
import os
# import musicbrainzngs

load_dotenv() # Load environment variables from .env.

# Create data directory if it doesn't exist
def ensure_data_directory():
    """Create data directory if it doesn't exist."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

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
    track_id = "1680a4c0-c47b-4adb-92ac-62185a51cbef" # No One Noticed by The Marias
    track_url = f"{base_url}/track/{track_id}/audio-features"
    
    try:
        response = requests.get(track_url, headers=headers)
        print(f"Track Details - Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Track details retrieved successfully.")
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Export to JSON file
            data_dir = ensure_data_directory()
            output_file = os.path.join(data_dir, 'reccobeats_sample_track.json')
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Data exported to: {output_file}")
            
        else:
            print(f"Failed to retrieve track details.")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error during GET request: {e}")

def get_reccobeats_multiple_tracks(spotify_ids):
    """
    Query the ReccoBeats GET multiple track endpoint using one or more Spotify track IDs.
    Exports the result to data/reccobeats_multiple_tracks.json.
    """
    base_url = os.getenv("RECCOBEATS_API_URL")
    headers = {'Accept': 'application/json'}
    data_dir = ensure_data_directory()
    output_file = os.path.join(data_dir, 'reccobeats_multiple_tracks.json')

    # Remove the space after 'ids='
    ids_params = '&'.join([f'ids={sid}' for sid in spotify_ids])
    url = f"{base_url}/track?{ids_params}"

    print(f"Requesting: {url}")
    try:
        response = requests.get(url, headers=headers)
        print(f"ReccoBeats Multiple Track Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"ReccoBeats multiple track result exported to: {output_file}")
            return data
        else:
            print("ReccoBeats multiple track request failed.")
            print(response.text)
            with open(output_file, 'w') as f:
                json.dump({"error": response.text}, f, indent=2)
            print(f"Error response exported to: {output_file}")
            return None
    except Exception as e:
        print(f"Error during ReccoBeats GET multiple track request: {e}")
        return None

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
    top_tracks_url = f"{base_url}?method=chart.gettoptracks&api_key={api_key}&format=json" # Default limit is 50 tracks
    
    try:
        response = requests.get(top_tracks_url)
        print(f"Top Tracks - Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Top tracks retrieved successfully.")
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Export to JSON file
            data_dir = ensure_data_directory()
            output_file = os.path.join(data_dir, 'lastfm_top_tracks.json')
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Data exported to: {output_file}")
            
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

    all_works_data = []

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
            
            work_data = {
                "mbid": mbid,
                "title": title,
                "language": detailed_work.get('language'),
                "artist_relations": detailed_work.get('artist-relation-list'),
                "tags": detailed_work.get('tag-list')
            }
            all_works_data.append(work_data)
            
            print(f"Title: {title}")
            print(f"Language: {detailed_work.get('language')}")
            print(f"Artist Relations: {detailed_work.get('artist-relation-list')}")
            print(f"Tags: {detailed_work.get('tag-list')}")
            print("---")
        except Exception as e:
            print(f"Error fetching details for {title}: {e}")
    
    # Export to JSON file
    if all_works_data:
        data_dir = ensure_data_directory()
        output_file = os.path.join(data_dir, 'musicbrainz_rap_works.json')
        with open(output_file, 'w') as f:
            json.dump(all_works_data, f, indent=2)
        print(f"MusicBrainz data exported to: {output_file}")

def search_spotify_track_artist(song_title, artist_name):
    """
    Search Spotify for a track and artist using the /v1/search endpoint.
    Export the result to data/spotify_search_result.json.
    """
    # Get Spotify API credentials from environment
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    # Get access token using Client Credentials Flow
    auth_response = requests.post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        auth=(client_id, client_secret)
    )
    if auth_response.status_code != 200:
        print("Failed to authenticate with Spotify API.")
        print(auth_response.text)
        return None
    access_token = auth_response.json()['access_token']
    
    # Build query
    query = f"{song_title} {artist_name}"
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": query,
        "type": "track,artist",
        "market": "US",
        "include_external": "audio"
    }
    
    response = requests.get(url, headers=headers, params=params)
    print(f"Spotify Search Status: {response.status_code}")
    data_dir = ensure_data_directory()
    output_file = os.path.join(data_dir, 'spotify_search_result.json')
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        # Export to JSON file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Spotify search result exported to: {output_file}")
        return data
    else:
        print("Spotify search failed.")
        print(response.text)
        # Still export the error response for debugging
        with open(output_file, 'w') as f:
            json.dump({"error": response.text}, f, indent=2)
        print(f"Error response exported to: {output_file}")
        return None

if __name__ == "__main__":
    test_reccobeats_api()
    print("ReccoBeats API tests completed.")
    # ----------------------------------------
    # test_lastfm_api()
    # print("Last.fm API tests completed.")
    # ----------------------------------------
    # top_song = {
    #     "name": "No One Noticed",
    #     "artist": {"name": "The Marias"}
    # }
    # print("\n--- Spotify Search for Top Last.fm Song ---")
    # search_spotify_track_artist(top_song["name"], top_song["artist"]["name"])
    # ----------------------------------------
    # test_musicbrainz()
    # print("MusicBrainz API tests completed.")
    # ----------------------------------------
    # print("\n--- ReccoBeats GET Multiple Track API ---")
    # get_reccobeats_multiple_tracks(["3siwsiaEoU4Kuuc9WKMUy5"])
    
    
# 1 Pull top 50 charting songs from Last.fm
# 2 Use Spotify's Search for Item endpoint (GET /search) to search for the 
# song by its title and artist name in the query parameters
# and also filter type to be album and track.
# 3. Parse the data file^ to find the spotify track id. NEED TO HANDLE
# 4. Now that we have found the spotify track ID, we can use the ReccoBeats API's GET MULTIPLE TRACK endpoint with 1 to 40 different spotify track ids to retrieve the ReccoBeats unique track id for the track(s)
# 5. Then using the reccobeats id, we can use the get track's audio features endpoint to get the audio features.

# Top song from Last.fm data:
# {
#         "name": "The Subway",
#         "duration": "252",
#         "playcount": "3590115",
#         "listeners": "436890",
#         "mbid": "1239f0bf-6874-4ea4-ac0e-8c1c0207eb7f",
#         "url": "https://www.last.fm/music/Chappell+Roan/_/The+Subway",
#         "streamable": {
#           "#text": "0",
#           "fulltrack": "0"
#         },
#         "artist": {
#           "name": "Chappell Roan",
#           "mbid": "56a55378-f155-48de-80a5-d80104221267",
#           "url": "https://www.last.fm/music/Chappell+Roan"
#         },
#         "image": [
#           {
#             "#text": "https://lastfm.freetls.fastly.net/i/u/34s/2a96cbd8b46e442fc41c2b86b821562f.png",
#             "size": "small"
#           },
#           {
#             "#text": "https://lastfm.freetls.fastly.net/i/u/64s/2a96cbd8b46e442fc41c2b86b821562f.png",
#             "size": "medium"
#           },
#           {
#             "#text": "https://lastfm.freetls.fastly.net/i/u/174s/2a96cbd8b46e442fc41c2b86b821562f.png",
#             "size": "large"
#           },
#           {
#             "#text": "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png",
#             "size": "extralarge"
#           }
#         ]
#       },

# SPOTIFY TRACK SEARCH RESULT
# "href": "https://api.spotify.com/v1/tracks/2SsY5k7UWFqgye3PUMG3Oq",
#         "id": "2SsY5k7UWFqgye3PUMG3Oq",
#         "is_local": false,
#         "is_playable": true,
#         "name": "The Subway",
#         "popularity": 90,
#         "preview_url": null,
#         "track_number": 1,
#         "type": "track",
#         "uri": "spotify:track:2SsY5k7UWFqgye3PUMG3Oq"
# So The Subway by Chappell Roan is not available on Reccobeats