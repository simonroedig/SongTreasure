import os
import random
import sys
import logging as log
from flask import redirect, request, session
import datetime
import keras
import spotipy
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import FlaskSessionCacheHandler
from dotenv import load_dotenv
import pandas as pd

global offset
offset = 0# Global variable to keep track of the current offset

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


def get_newest_tracks(genre, limit=50, timeframe="day", market="DE"):
    global offset
    client_id, client_secret, redirect_uri = get_env_vars()
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    end_date = datetime.date.today()

    if timeframe == 'year':
        start_date = end_date.replace(year=end_date.year - 1)
    elif timeframe == 'month':
        start_date = (end_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=end_date.day)
    elif timeframe == 'week':
        start_date = end_date - datetime.timedelta(weeks=1)
    elif timeframe == 'day':
        start_date = end_date - datetime.timedelta(days=1)
    else:
        raise ValueError("Invalid timeframe. Choose 'year', 'month', 'week', or 'day'.")

    global offset
    tracks = []
    max_offset = 1000

    while len(tracks) < limit and offset < max_offset:
        query = f'genre:{genre} year:{start_date.year}-{end_date.year}'
        results = sp.search(q=query, type='track', limit=limit, market=market, offset=offset)
        new_tracks = results['tracks']['items']

        if not new_tracks:
            break

        for track in new_tracks:
            release_date = datetime.datetime.strptime(track['album']['release_date'], '%Y-%m-%d').date()
            if start_date <= release_date <= end_date:
                tracks.append(track)
                if len(tracks) == limit:
                    break

        offset += limit

    tracks.sort(key=lambda x: x['album']['release_date'], reverse=True)
    return tracks

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
            'popularity': track['predicted_popularity'],
            'release_date': formatted_release_date,
            'album': track['album']['name'] if 'name' in track['album'] else 'Album not available',
        }
        track_info.append(track_details)
    
    return track_info

def load_model():
    model = keras.models.load_model('model.keras')
    return model

def predict_popularity(metadata):
    model = load_model()
    prediction = model.predict(metadata)
    return prediction

def get_audio_features(track_ids):
    client_id, client_secret, redirect_uri = get_env_vars()
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    
    return sp.audio_features(tracks=track_ids)

def filter_relevant_audio_features(track_metadata):
    relevant_keys = {
        "acousticness", "danceability", "duration_ms", "energy",
        "instrumentalness", "liveness", "loudness", "speechiness",
        "tempo", "valence", "key", "mode", "time_signature"
    }
    # Add a check to handle different structures
    if isinstance(track_metadata, list):
        track_metadata = track_metadata[0]  # Assuming the list contains one dict

    filtered_metadata = {key: track_metadata[key] for key in relevant_keys if key in track_metadata}
    return filtered_metadata
    
def create_df_from_track_metadata(track_metadata):
    # Ensure each value is a list
    track_metadata = {k: [v] if not isinstance(v, list) else v for k, v in track_metadata.items()}
    df = pd.DataFrame(track_metadata)
    sorted_df = df.sort_index(axis=1)
    return sorted_df

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



