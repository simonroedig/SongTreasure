# Python 3.11.0
import os
from flask import Flask, jsonify, render_template, request, redirect, session, send_from_directory
import spotifyAPI
from dotenv import load_dotenv
import datetime

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
sp_oauth, cache_handler, sp = spotifyAPI.init_oauth()

tracks = []
tracks_for_frontend = []
isLoggedIn = False
user_playlists = []

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'static/favicon.png', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    global isLoggedIn
    global tracks
    global tracks_for_frontend
    global user_playlists

    profile_pic_url = None
    if isLoggedIn:
        try:
            user_info = sp.current_user()
            profile_pic_url = user_info['images'][0]['url'] if user_info['images'] else None
            
            user_playlists = sp.current_user_playlists()['items']
            user_playlists = [{'name': playlist['name'], 'id': playlist['id']} for playlist in user_playlists]
            

        except:
            profile_pic_url = None
            
            user_playlists = []
            print("ERROR: Could not get user info")

    print(user_playlists)
    return render_template(
        'index.html',
        isLoggedIn=isLoggedIn,
        tracks=tracks_for_frontend,
        tracks_ammount=len(tracks),
        current_year=datetime.datetime.now().year,
        profile_pic_url=profile_pic_url,
        user_playlists=user_playlists
    )


@app.get('/login')
def login():
    global isLoggedIn
    isLoggedIn = True
    return spotifyAPI.validate_token(sp_oauth, cache_handler)

@app.route('/callback')
def callback():
    return spotifyAPI.store_token(sp_oauth)

@app.route('/logout')
def logout():
    session.clear()
    global isLoggedIn
    isLoggedIn = False
    print("Logged out")
    return redirect('/')

@app.route('/find_songs', methods=['POST'])
def post_endpoint():
    global user_playlists
    
    data = request.json
    genre = data.get('genre')
    songs = data.get('songs')
    
    if (genre is None or genre == '') or (songs is None or songs == ''):
        return jsonify({
        'tracks': 0,
        'tracks_ammount': 0
    })
    
    songs = int(songs)
    response = (genre, songs)
    # print(response)
    
    global tracks
    
    requested_track_ammount = songs + 10
    newest_tracks = spotifyAPI.get_newest_tracks(genre, requested_track_ammount)
        
    for track in newest_tracks:
        current_track_id = track['id']
        
        track_metadata = spotifyAPI.get_audio_features(current_track_id)
        
        # this give us a dictionary with the relevant audio features
        track_relevant_metadata = spotifyAPI.filter_relevant_audio_features(track_metadata)
        # print(track_relevant_metadata)
        
        track_metadata_df = spotifyAPI.create_df_from_track_metadata(track_relevant_metadata)
        
        predicted_popularity = (spotifyAPI.predict_popularity(track_metadata_df))[0][0]
        track['predicted_popularity'] = int(predicted_popularity)
        
        # print("-------------------------------------------------")
        # print(predicted_popularity)
        # print("-------------------------------------------------")
        
        
    sorted_tracks_with_pop = sorted(newest_tracks, key=lambda x: x['predicted_popularity'], reverse=True)
    sorted_tracks_with_pop_stripped = sorted_tracks_with_pop[:songs]
    
    # print(sorted_tracks_with_pop_stripped)

    
    global tracks_for_frontend
    tracks_for_frontend = spotifyAPI.get_track_information_to_display_in_frontend(sorted_tracks_with_pop_stripped)
    
    # print(tracks)
    # print('_________________________________________')
    # print(tracks_for_frontend)
    
    # keep returning this, as it is the only way to get the data to the frontend
    return jsonify({
        'tracks': tracks_for_frontend,
        'tracks_ammount': len(sorted_tracks_with_pop_stripped)
    })


@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    data = request.json
    playlist_id = data['playlist_id']
    track_id = data['track_id']

    try:
        # Check if the track is already in the playlist
        playlist_tracks = sp.playlist_tracks(playlist_id)
        track_ids = [item['track']['id'] for item in playlist_tracks['items']]
        
        if track_id in track_ids:
            return jsonify(success=False, error='track_in_playlist_already')

        # Add the track to the playlist
        sp.playlist_add_items(playlist_id, [track_id])
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))
    
@app.route('/ckeck_track_playlist', methods=['POST'])
def ckeck_track_playlist():
    data = request.json
    playlist_id = data['playlist_id']
    track_id = data['track_id']

    try:
        # Check if the track is already in the playlist
        playlist_tracks = sp.playlist_tracks(playlist_id)
        track_ids = [item['track']['id'] for item in playlist_tracks['items']]
        
        if track_id in track_ids:
            return jsonify(success=True)
        else:
            return jsonify(success=False)
    except Exception as e:
        return jsonify(success=False, error=str(e))
    
if __name__ == '__main__':
    if os.getenv('MODE') == 'DEV':
        app.run(debug=True, host='0.0.0.0', port=8080)
