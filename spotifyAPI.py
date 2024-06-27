import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import sys

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')


def read_env_file(file_path):
    env_vars = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Remove any leading/trailing whitespace
                line = line.strip()
                
                # Ignore empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Split key and value
                key, value = line.split('=', 1)
                
                # Remove leading/trailing quotes from value if present
                value = value.strip('\'"')
                
                # Store in dictionary
                env_vars[key] = value
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"Error: An error occurred while reading the file: {e}")
    
    return env_vars

env_file_path = '.env'
env_vars = read_env_file(env_file_path)
spotify_client_id = env_vars.get('SPOTIFY_CLIENT_ID', '')
spotify_client_secret = env_vars.get('SPOTIFY_CLIENT_SECRET', '')
print(spotify_client_id + " " + spotify_client_secret)

client_credentials_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


# Function to get newest tracks in a genre
def get_newest_tracks(genre, limit=50):
    today = datetime.date.today()
    query = f'genre:{genre} year:{today.year}'
    results = sp.search(q=query, type='track', limit=50, market='US')
    tracks = results['tracks']['items']

    # Fetch additional tracks if necessary
    while len(tracks) < limit:
        results = sp.search(q=query, type='track', limit=50, market='US', offset=len(tracks))
        tracks.extend(results['tracks']['items'])
        if len(results['tracks']['items']) == 0:
            break

    # Sort the tracks by release date (newest first)
    tracks_sorted = sorted(tracks, key=lambda x: x['album']['release_date'], reverse=True)
    return tracks_sorted[:limit]

# Function to get audio features for a list of track IDs
def get_audio_features(track_ids):
    features = sp.audio_features(tracks=track_ids)
    return {feature['id']: feature for feature in features}

# Function to print track metadata
def print_track_metadata(track, audio_features, genre):
    artists = ", ".join([artist['name'] for artist in track['artists']])
    album = track['album']
    track_id = track['id']
    features = audio_features.get(track_id, {})

    print(f"Track ID: {track_id}")
    print(f"Track Name: {track['name']}")
    print(f"Artists: {artists}")
    print(f"Album Name: {album['name']}")
    print(f"Release Date: {album['release_date']}")
    print(f"Popularity: {track['popularity']}")
    print(f"Duration (ms): {track['duration_ms']}")
    print(f"Explicit: {track['explicit']}")
    print(f"Track URI: {track['uri']}")
    print(f"Track Genre: {genre}")
    print(f"Danceability: {features.get('danceability', 'N/A')}")
    print(f"Energy: {features.get('energy', 'N/A')}")
    print(f"Key: {features.get('key', 'N/A')}")
    print(f"Loudness: {features.get('loudness', 'N/A')}")
    print(f"Mode: {features.get('mode', 'N/A')}")
    print(f"Speechiness: {features.get('speechiness', 'N/A')}")
    print(f"Acousticness: {features.get('acousticness', 'N/A')}")
    print(f"Instrumentalness: {features.get('instrumentalness', 'N/A')}")
    print(f"Liveness: {features.get('liveness', 'N/A')}")
    print(f"Valence: {features.get('valence', 'N/A')}")
    print(f"Tempo: {features.get('tempo', 'N/A')}")
    print(f"Time Signature: {features.get('time_signature', 'N/A')}")
    print("-" * 50)
    
genre = 'rock'

newest_rock_tracks = get_newest_tracks(genre, limit=50)

# Get track IDs
track_ids = [track['id'] for track in newest_rock_tracks]

# Get audio features for the tracks
audio_features = get_audio_features(track_ids)

# Print the results
for idx, track in enumerate(newest_rock_tracks):
    print(f"{idx + 1}:")
    print_track_metadata(track, audio_features, genre)