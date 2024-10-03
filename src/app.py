import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from authentication import get_spotify_oauth

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def convert_duration(ms):
    mins = ms // 60000
    secs = (ms % 60000) // 1000

    return f"{mins}:{secs:02d}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()

    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/callback')
def callback():
    sp_oauth = get_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info

    return redirect(url_for('recently_played'))

@app.route('/artists')
def top_artists():
    token_info = session.get("token_info", None)

    if not token_info:
        return redirect(url_for('login'))

    sp_oauth = get_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    sp = Spotify(auth=token_info['access_token'])

    time_range = request.args.get('time', 'short_term')

    try:
        results = sp.current_user_top_artists(limit=50, time_range=time_range)
    except SpotifyException as e:
        if e.http_status == 401:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
            sp = Spotify(auth=token_info['access_token'])
            results = sp.current_user_top_artists(limit=50, time_range='short_term')
        else:
            raise e

    artists = []

    for item in results['items']:
        artist_name = item['name']
        artist_url = item['external_urls']['spotify']
        cover_art = item['images'][0]['url']
        genres = ', '.join(item['genres'])
        followers = item['followers']['total']
        popularity = item['popularity']
 
        artist = {
            'name': artist_name,
            'artist_url': artist_url,
            'cover_art': cover_art,
            'genres': genres,
            'followers': followers,
            'popularity': popularity
        }

        artists.append(artist)

    return render_template('top_artists.html', artists=artists, enumerate=enumerate)

@app.route('/tracks')
def top_tracks():
    token_info = session.get("token_info", None)

    if not token_info:
        return redirect(url_for('login'))

    sp_oauth = get_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    sp = Spotify(auth=token_info['access_token'])

    time_range = request.args.get('time', 'short_term')

    try:
        results = sp.current_user_top_tracks(limit=50, time_range=time_range)
    except SpotifyException as e:
        if e.http_status == 401:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
            sp = Spotify(auth=token_info['access_token'])
            results = sp.current_user_top_tracks(limit=50, time_range='short_term')
        else:
            raise e

    tracks = []

    for item in results['items']:
        track_name = item['name']
        artist_name = item['artists'][0]['name']
        artist_url = item['artists'][0]['external_urls']['spotify']
        cover_art = item['album']['images'][0]['url']
        album_name = item['album']['name']
        release_date = item['album']['release_date']
        track_duration = convert_duration(item['duration_ms'])
        song_url = item['external_urls']['spotify']
        popularity = item['popularity']

        track = {
            'artist': artist_name,
            'artist_url': artist_url,
            'name': track_name,
            'cover_art': cover_art,
            'album': album_name,
            'release_date': release_date,
            'duration': track_duration,
            'song_url': song_url,
            'popularity': popularity
        }
        tracks.append(track)

    return render_template('top_tracks.html', tracks=tracks, enumerate=enumerate)

@app.route('/tracks/recent')
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

    tracks = []

    for item in results['items']:
        track_name = item['track']['name']
        artist_name = item['track']['artists'][0]['name']
        artist_url = item['track']['artists'][0]['external_urls']['spotify']
        cover_art = item['track']['album']['images'][0]['url']
        song_url = item['track']['external_urls']['spotify']
        played_at = datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d/%m/%y, %H:%M')

        track = {
            'artist': artist_name,
            'artist_url': artist_url,
            'name': track_name,
            'cover_art': cover_art,
            'song_url': song_url,
            'played_at': played_at
        }
        tracks.append(track)

    return render_template('recently_played.html', tracks=tracks, enumerate=enumerate)


if __name__ == "__main__":
    app.run(debug=True)
