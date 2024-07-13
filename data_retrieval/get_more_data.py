import itertools
import logging
import random
import time
from base64 import b64encode

import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os
import dotenv

dotenv.load_dotenv()

spotify_client_and_secrets_list = [
    {
        "client_id": "a77f36c1ce174b2099b7cf721f2b1d9a",
        "client_secret": "9cbdb8af43724676abae908df2f6c6b7",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "test_app_y"
    },
    {
        "client_id": "58ae849b1b284409a0abe0b526dc3fa7",
        "client_secret": "7d0f3ed3ca3041c29b58c9da5760a739",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "spotify_api_y"
    },
    {
        "client_id": "c45d40851eb64f2191349ef26ddf89d1",
        "client_secret": "00ae45ac576a464fa1c4eb078b66927e",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "spotify_app_y"
    },
    {
        "client_id": "ed66ebcec8964eeea44b7f8cf81939fe",
        "client_secret": "195ebc2a4e9744fbb4ae329401cd1423",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "api_tester_y"
    },
    {
        "client_id": "6941ff8f63044903ae8579b6864115bb",
        "client_secret": "7ac017bfd3884a4788a28ba28e485323",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_l"
    },
    {
        "client_id": "8bb91dc132884b7382338ec0add7101b",
        "client_secret": "546868168362404d821f97f996c651a6",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_l"
    },
    {
        "client_id": "768f4b547e4c48b6ab983aff3c479dd9",
        "client_secret": "25b2caad5ee2431d9f7e475add8b295b",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_l"
    },
    {
        "client_id": "25459af0f2934ee892e39bb08db86713",
        "client_secret": "c102ff52a44443dda673f1d056516f45",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_l"
    },
    {
        "client_id": "c5106f1a04814cb5bd286303f797478f",
        "client_secret": "94e7fd0b556143a0a393dbcd9e440c4b",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_s"
    },
    {
        "client_id": "917590d01dcc4115accaa655e560c827",
        "client_secret": "fc34dd10e69642219667bcd2c05746cc",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_s"
    },
    {
        "client_id": "86d33c2b9c484ca4a674f645403cb726",
        "client_secret": "4595da98f3f04a3bb063d1a10ee7aa0c",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_s"
    },
    {
        "client_id": "34f4094b951247d89051fa4e6a406ed9",
        "client_secret": "7ae9aeb64f5245e08ef57ebb74ee1dcd",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_s"
    },
    {
        "client_id": "baf2668c2eba4e949971072a50b3fe40",
        "client_secret": "fd20eb429b73423eb4cf571fcc1016c0",
        "redirect_uri": "http://localhost:8888/callback",
        "app_name": "API_s"
    }
]

RATE_LIMIT_RETRY_DELAY = 30 * 60  # 30 minutes
GET_MOST_POPULAR_SONGS = False

# List of random genres to choose from
genres = ["acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime", "black-metal", "bluegrass", "blues",
          "bossanova", "brazil", "breakbeat", "british", "cantopop", "chicago-house", "children", "chill", "classical",
          "club", "comedy", "country", "dance", "dancehall", "death-metal", "deep-house", "detroit-techno", "disco",
          "disney", "drum-and-bass", "dub", "dubstep", "edm", "electro", "electronic", "emo", "folk", "forro", "french",
          "funk", "garage", "german", "gospel", "goth", "grindcore", "groove", "grunge", "guitar", "happy", "hard-rock",
          "hardcore", "hardstyle", "heavy-metal", "hip-hop", "holidays", "honky-tonk", "house", "idm", "indian",
          "indie", "indie-pop", "industrial", "iranian", "j-dance", "j-idol", "j-pop", "j-rock", "jazz", "k-pop",
          "kids", "latin", "latino", "malay", "mandopop", "metal", "metal-misc", "metalcore", "minimal-techno",
          "movies", "mpb", "new-age", "new-release", "opera", "pagode", "party", "philippines-opm", "piano", "pop",
          "pop-film", "post-dubstep", "power-pop", "progressive-house", "psych-rock", "punk", "punk-rock", "r-n-b",
          "rainy-day", "reggae", "reggaeton", "road-trip", "rock", "rock-n-roll", "rockabilly", "romance", "sad",
          "salsa", "samba", "sertanejo", "show-tunes", "singer-songwriter", "ska", "sleep", "songwriter", "soul",
          "soundtracks", "spanish", "study", "summer", "swedish", "synth-pop", "tango", "techno", "trance", "trip-hop",
          "turkish", "work-out", "world-music"]

# Relevant keys for audio features
relevant_keys = {
    "id", "track_name", "popularity", "acousticness", "danceability", "duration_ms", "energy",
    "instrumentalness", "liveness", "loudness", "speechiness",
    "tempo", "valence", "key", "mode", "time_signature",
}


# Function to handle the search request with retries
def perform_search(year_span, max_retries, n, sp):
    attempts = 0
    max_offset = 800  # Limit offset to a reasonable number
    while attempts < max_retries:
        offset = random.randint(0, max_offset)
        try:
            # logging.warning(f"Spotify Request: Searching for tracks from {year_span} at offset {offset}...")
            # random_tracks = sp.search(q=f'year:{year_span}', type='track', limit=n, offset=offset)
            random_tracks = sp.search(q=f'year:{year_span}', type='track', limit=n, offset=offset)
            if not random_tracks['tracks']['items']:
                # If no tracks are found, reduce the offset or handle appropriately
                print(f"No tracks found at offset {offset} for year {year_span}. Reducing offset.")
                offset = max(0, offset - 100)  # Safely reduce offset
                continue
            return random_tracks
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                print(f"Rate limited on . Retrying after {RATE_LIMIT_RETRY_DELAY} seconds.")
                time.sleep(RATE_LIMIT_RETRY_DELAY)
            elif e.http_status == 400:
                # Handle bad request error
                print(f"Bad request at offset {offset}. Adjusting offset.")
                offset = max(0, offset - 50)  # Adjust offset downward
                continue
            else:
                print(f"Failed to fetch songs: {e}")
                raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        attempts += 1
    print("Max retries exceeded.")
    return None


def perform_recommendations(seed_genres, max_retries, n, sp, target_popularity):
    attempts = 0
    # get random 5 genres
    seed_genres = random.sample(seed_genres, 5)

    while attempts < max_retries:
        try:
            # Logging the attempt (uncomment if needed)
            print(f"Spotify Request: Getting recommendations with target popularity {target_popularity}...")
            recommendations = sp.recommendations(seed_genres=seed_genres, limit=n, target_popularity=target_popularity)
            print(f'Successfully fetched recommendations with target popularity {target_popularity}.')
            if not recommendations['tracks']:
                print(f"No recommendations found with target popularity {target_popularity}. Retrying...")
                attempts += 1
                continue

            return recommendations
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                print(f"Rate limited. Retrying after {RATE_LIMIT_RETRY_DELAY} seconds.")
                time.sleep(RATE_LIMIT_RETRY_DELAY)
            else:
                print(f"Failed to fetch recommendations: {e}")
                raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        attempts += 1

    print("Max retries exceeded.")
    return None


# Function to get audio features with retries
def get_access_token(client_id, client_secret):
    """
    Get Spotify access token using client credentials flow.

    Parameters:
        client_id (str): Spotify API client ID.
        client_secret (str): Spotify API client secret.

    Returns:
        str: Access token.
    """
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        logging.error(f"Failed to get access token: {response.status_code} {response.text}")
        return None


def get_features(track_ids, access_token, max_retries=5):
    """
    Fetch audio features for the given list of track IDs from Spotify.

    Parameters:
        track_ids (list): List of Spotify track IDs.
        access_token (str): Spotify API access token.
        max_retries (int): Maximum number of retries in case of rate limiting.

    Returns:
        list: List of audio features for the given tracks.
    """
    url = "https://api.spotify.com/v1/audio-features"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "ids": ",".join(track_ids)
    }

    # logging.warning(f"Spotify Request: Fetching audio features for {len(track_ids)} tracks...")

    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            features = response.json().get('audio_features')
            return features
        elif response.status_code == 429:
            logging.warning(f"Rate limited. Retrying after {RATE_LIMIT_RETRY_DELAY} seconds.")
            time.sleep(RATE_LIMIT_RETRY_DELAY)
        else:
            logging.error(f"Failed to fetch audio features: {response.status_code} {response.text}")
            break

    logging.error("Max retries exceeded.")
    return None


def get_100_of_most_popular_songs_from_dataset(offset=0):
    # Load the dataset
    df = pd.read_csv('datasets/random_songs.csv')
    # Get 100 songs from the dataset with offset as array
    return df.iloc[offset:offset + 100].to_dict(orient='records')


# Function to get random tracks with their features
def get_random_tracks_with_features(n, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, target_popularity, offset=0):
    # Authenticate
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    tracks = []
    max_retries = 10

    # Get a random offset and year span
    year_span = random.randint(1995, 2024)

    # Perform the search request
    results = perform_search(year_span, max_retries, n, sp)
    # if GET_MOST_POPULAR_SONGS:
    #     results = get_100_of_most_popular_songs_from_dataset(offset=offset)
    # else:
    #     results = perform_recommendations(genres, max_retries, n, sp, target_popularity)

    if results:
        if GET_MOST_POPULAR_SONGS:
            tracks.extend(results)
        else:
            tracks.extend(results['tracks']['items'])
        tracks = tracks[:n]

        # Extract track IDs
        track_ids = [track['id'] for track in tracks]

        # Get features for these tracks
        features = get_features(track_ids, get_access_token(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET), max_retries=10)

        if features:
            # Combine track info with their features
            track_data = []
            for track, feature in zip(tracks, features):
                if feature:  # Ensure feature data is available
                    track_info = {
                        "track_name": track['name'],
                        "artist": track['artists'][0]['name'],
                        "id": track['id'],
                        "popularity": track['popularity'],
                        "acousticness": feature["acousticness"],
                        "danceability": feature["danceability"],
                        "duration_ms": feature["duration_ms"],
                        "energy": feature["energy"],
                        "instrumentalness": feature["instrumentalness"],
                        "liveness": feature["liveness"],
                        "loudness": feature["loudness"],
                        "speechiness": feature["speechiness"],
                        "tempo": feature["tempo"],
                        "valence": feature["valence"],
                        "key": feature["key"],
                        "mode": feature["mode"],
                        "time_signature": feature["time_signature"]
                    }
                    track_data.append(track_info)

            # # Create DataFrame and save to CSV
            # df = pd.DataFrame(track_data)
            # df.to_csv('random_songs.csv', index=False)
            #
            # print("CSV file 'random_songs.csv' has been created successfully.")
            return track_data
        else:
            print("Failed to fetch audio features.")
            return []
    else:
        print("Failed to fetch tracks.")
        return []


def main():
    start_time = time.time()
    # Fetch 10 random songs
    total_songs_num = 1_000_000
    max_songs_per_request = 50

    # Create an iterator that cycles through the client data
    client_cycle = itertools.cycle(spotify_client_and_secrets_list)
    next(client_cycle)
    # Create an empty list to store the random tracks with features
    random_tracks_with_features = []

    milestone = len(pd.read_csv('datasets/random_songs.csv')) + 1000

    # time.sleep(3 * 60 * 60)  # Sleep for 3 hours (to avoid rate limiting
    offset = 0
    while len(pd.read_csv('datasets/random_songs.csv')) < total_songs_num:
        time.sleep(1)

        num_songs = min(max_songs_per_request, total_songs_num - len(random_tracks_with_features))

        # Get the next client from the cycle
        current_client = next(client_cycle)

        SPOTIPY_CLIENT_ID = current_client['client_id']
        SPOTIPY_CLIENT_SECRET = current_client['client_secret']
        app_name = current_client['app_name']

        #print(f'Using client ID: {SPOTIPY_CLIENT_ID} and Secret: {SPOTIPY_CLIENT_SECRET} for {app_name}')

        df = pd.read_csv('datasets/random_songs.csv')

        # Check which popularity is the least common, and get songs with that popularity
        target_popularity = df['popularity'].value_counts().idxmin()

        #print(f"Getting {num_songs} songs with popularity {target_popularity} because we only have this many songs with this popularity: {df['popularity'].value_counts().min()}")

        new_tracks = get_random_tracks_with_features(num_songs, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET,
                                                     target_popularity, offset=offset)
        offset += max_songs_per_request

        random_tracks_with_features.extend(new_tracks)

        # Create a list of dictionaries with the relevant keys
        data = []
        for track in new_tracks:
            track_data = {key: track[key] for key in track.keys()}  # assuming all keys are relevant
            data.append(track_data)

        # Create DataFrame
        df = pd.DataFrame(data)

        # Append to CSV, create if not exists
        with open('datasets/random_songs.csv', 'a') as f:
            df.to_csv(f, index=False, header=f.tell() == 0)
        with open('datasets/random_songs_recommendations.csv', 'a') as f:
            df.to_csv(f, index=False, header=f.tell() == 0)

        # print(f"Added {num_songs} songs to 'random_songs.csv'")
        number_of_songs = len(pd.read_csv('datasets/random_songs.csv'))
        # Print how many songs in csv
        if number_of_songs >= milestone:
            formatted_number_of_songs = "{:,}".format(number_of_songs)
            print(f"Total songs in 'random_songs.csv': {formatted_number_of_songs}")
            milestone += 500

        #print(f"Total songs in 'random_songs.csv': {len(pd.read_csv('datasets/random_songs.csv'))}")

    print("CSV file 'random_songs.csv' has been updated successfully.")
    print(f"Total time elapsed: {round(time.time() - start_time, 2)}s")


if __name__ == "__main__":
    main()
