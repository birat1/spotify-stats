import os
from flask import Flask, redirect, render_template, request, session, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from authentication import get_spotify_oauth

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()

    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = get_spotify_oauth()
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
    
    sp_oauth = get_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info


    sp = Spotify(auth=token_info['access_token'])

    try:
        results = sp.current_user_recently_played(limit=50)
    except SpotifyException as e:
        if e.http_status == 401:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
            sp = Spotify(auth=token_info['access_token'])
            results = sp.current_user_recently_played(limit=50)
        else:
            raise e

    seen_tracks = set()
    unique_tracks = []

    for item in results['items']:
        track_name = item['track']['name']
        artist_name = item['track']['artists'][0]['name']
        cover_art = item['track']['album']['images'][0]['url']
        track = (artist_name, track_name, cover_art)

        if track not in seen_tracks:
            seen_tracks.add(track)
            unique_tracks.append(track)

    return render_template('recently_played.html', tracks=unique_tracks)


if __name__ == "__main__":
    app.run(debug=True)