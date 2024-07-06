import os
import sys
import logging as log
from flask import redirect, request, session
import datetime
import spotipy
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import FlaskSessionCacheHandler
from dotenv import load_dotenv

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
scope = ("user-library-read "
         "playlist-read-private "
         "playlist-read-collaborative "
         "playlist-modify-public "
         "playlist-modify-private")

def get_env_vars():
    #Loads all environment variables from the .env file
    try:
        load_dotenv()
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        if os.getenv('MODE') == 'DEV':
            redirect_uri = os.getenv('REDIRECT_URI_DEV')
        else:
            redirect_uri = os.getenv('REDIRECT_URI')

        if not client_id:
            raise ValueError("Missing Spotify Client ID")
        if not client_secret:
            raise ValueError("Missing Spotify Client Secret")
        log.info("Client ID and Client Secret found")
        return client_id, client_secret, redirect_uri
    except Exception as e:
        log.error(f"Error: An error occurred while reading the environment variables: {e}")
        sys.exit(1)


def init_oauth():
    client_id, client_secret, redirect_uri = get_env_vars()
    cache_handler = FlaskSessionCacheHandler(session)
    sp_oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_handler=cache_handler,
        show_dialog=True
    )
    sp = Spotify(auth_manager=sp_oauth)
    print("Initialized Spotify OAuth")
    return sp_oauth, cache_handler, sp


def validate_token(sp_oauth, cache_handler):
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        print("No valid token found, redirecting to Spotify login")
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    print("Valid token found, redirecting to index")
    return redirect("/")


def store_token(sp_oauth):
    sp_oauth.get_access_token(request.args['code'])
    return redirect('/')


def get_newest_tracks(genre, limit):
    client_id, client_secret = get_env_vars()
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    today = datetime.date.today()
    query = f'genre:{genre} year:{today.year}'
    results = sp.search(q=query, type='track', limit=limit, market='US')
    tracks = results['tracks']['items']

    # Fetch additional tracks if necessary
    while len(tracks) < limit:
        results = sp.search(q=query, type='track', limit=limit, market='US', offset=len(tracks))
        tracks.extend(results['tracks']['items'])
        if len(results['tracks']['items']) == 0:
            break

    return tracks


# Function to get audio features for a list of track IDs
def get_audio_features(track_ids):
    features = sp.audio_features(tracks=track_ids)
    return {feature['id']: feature for feature in features}


def get_track_information_to_display_in_frontend(track_list):
    # https://developer.spotify.com/documentation/web-api/reference/get-track
    track_info = []
    for track in track_list:
        minutes, seconds = divmod(track['duration_ms'] // 1000, 60)
        length_formatted = f"{minutes:02}:{seconds:02}"
        
        formatted_release_date = track['album']['release_date'] if 'release_date' in track['album'] else 'Date not available',
        # convert to string
        formatted_release_date = str(formatted_release_date[0])
        if formatted_release_date != 'Date not available':
            # Convert the string to a datetime object
            release_date_obj = datetime.datetime.strptime(formatted_release_date, '%Y-%m-%d')
            
            # Format the datetime object to the desired format
            formatted_release_date = release_date_obj.strftime('%b. %d, %Y')
        else:
            formatted_release_date = 'Date not available'
            
        track_details = {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'album_cover': track['album']['images'][0]['url'],
            'length': length_formatted,
            'preview_url': track['preview_url'] if track['preview_url'] else 'No preview available',
            'spotify_uri': track['uri'] if track['preview_url'] else 'No preview available',
            'popularity': track['popularity'],
            'release_date': formatted_release_date,
            'album': track['album']['name'] if 'name' in track['album'] else 'Album not available',
        }
        track_info.append(track_details)
    
    return track_info

# Function to print track metadata
def print_track_metadata(track, audio_features, genre):
    artists = ", ".join([artist['name'] for artist in track['artists']])
    album = track['album']
    track_id = track['id']
    features = audio_features.get(track_id, {})

    """
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
    """



