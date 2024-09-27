import os
from flask import Flask, redirect, render_template, request, session, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope='user-read-recently-played'
    )

    auth_url = sp_oauth.get_authorize_url()

    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope='user-read-recently-played'
    )

    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info

    return redirect(url_for('recently_played'))

@app.route('/recently-played')
def recently_played():
    token_info = session.get("token_info", None)

    if not token_info:
        return redirect(url_for('login'))

    sp = Spotify(auth=token_info['access_token'])
    results = sp.current_user_recently_played(limit=50)

    seen_tracks = set()
    unique_tracks = []

    for item in results['items']:
        track_name = item['track']['name']
        artist_name = item['track']['artists'][0]['name']
        track = (artist_name, track_name)

        if track not in seen_tracks:
            seen_tracks.add(track)
            unique_tracks.append(track)

    return render_template('recently_played.html', tracks=unique_tracks)


if __name__ == "__main__":
    app.run(debug=True)