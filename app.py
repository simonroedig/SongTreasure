# Python 3.9.13
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import spotifyAPI
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
sp_oauth, cache_handler, sp = spotifyAPI.init_oauth()

isLoggedIn = False


@app.route('/')
def index():
    return render_template('index.html', isLogedIn=isLoggedIn)

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
    return redirect('/')

@app.route('/find_songs', methods=['POST'])
def post_endpoint():
    data = request.json
    response = {"message": "Data received successfully", "received_data": data}
    print(response)
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)