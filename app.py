# Python 3.9.13
import os
from flask import Flask, jsonify, render_template, request, redirect, session, send_from_directory
import numpy as np
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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'static/favicon.png', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    global isLoggedIn
    global tracks
    global tracks_for_frontend

    profile_pic_url = None
    if isLoggedIn:
        try:
            user_info = sp.current_user()
            profile_pic_url = user_info['images'][0]['url'] if user_info['images'] else None
        except:
            profile_pic_url = None

    return render_template(
        'index.html',
        isLoggedIn=isLoggedIn,
        tracks=tracks_for_frontend,
        tracks_ammount=len(tracks),
        current_year=datetime.datetime.now().year,
        profile_pic_url=profile_pic_url
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
    print(response)
    
    global tracks
    tracks = spotifyAPI.get_newest_tracks(genre, songs)
    
    popularity_dict = {}
    
    for track in tracks:
        current_track_id = track['id']
        
        track_metadata = spotifyAPI.get_audio_features(current_track_id)
        print(track_metadata)
        
        print("-------------------------------------------------")
        
        # this give us a dictionary with the relevant audio features
        track_relevant_metadata = spotifyAPI.filter_relevant_audio_features(track_metadata)
        print(track_relevant_metadata)
        
        print("-------------------------------------------------")
        
        track_metadata_df = spotifyAPI.create_df_from_track_metadata(track_relevant_metadata)
        print(track_metadata_df)
        
        predicted_popularity = (spotifyAPI.predict_popularity(track_metadata_df))[0][0]
        
        print("-------------------------------------------------")
        print(predicted_popularity)
        print("-------------------------------------------------")
        
        popularity_dict[current_track_id] = predicted_popularity
        
    sorted_popularity_dict = {k: v for k, v in sorted(popularity_dict.items(), key=lambda item: item[1], reverse=True)}
    
    for i in range(len(songs)):
        
        
        
    
    global tracks_for_frontend
    tracks_for_frontend = spotifyAPI.get_track_information_to_display_in_frontend(tracks)
    
    #print(tracks)
    print('_________________________________________')
    #print(tracks_for_frontend)
    
    # keep returning this, as it is the only way to get the data to the frontend
    return jsonify({
        'tracks': tracks_for_frontend,
        'tracks_ammount': len(tracks)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)