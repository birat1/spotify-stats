import os
from dateutil import parser
from flask import Flask, redirect, render_template, request, session, url_for
from spotipy.exceptions import SpotifyException
from authentication import get_spotify_client, get_spotify_oauth, handle_spotify_exception

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
    sp, redirect_response = get_spotify_client()
    if redirect_response:
        return redirect_response

    time_range = request.args.get('time', 'short_term')

    try:
        results = sp.current_user_top_artists(limit=50, time_range=time_range)
    except SpotifyException as e:
        if handle_spotify_exception(e, session['token_info']):
            return top_artists()

    artists = []
    for item in results['items']:
        artist = {
            'name': item['name'],
            'artist_url': item['external_urls']['spotify'],
            'cover_art': item['images'][0]['url'],
            'genres': ', '.join(item['genres']),
            'followers': item['followers']['total'],
            'popularity': item['popularity']
        }

        artists.append(artist)

    return render_template('top_artists.html', artists=artists, enumerate=enumerate)

@app.route('/tracks')
def top_tracks():
    sp, redirect_response = get_spotify_client()
    if redirect_response:
        return redirect_response

    time_range = request.args.get('time', 'short_term')

    try:
        results = sp.current_user_top_tracks(limit=50, time_range=time_range)
    except SpotifyException as e:
        if handle_spotify_exception(e, session['token_info']):
            return top_tracks()

    tracks = []
    for item in results['items']:
        track = {
            'artist': item['artists'][0]['name'],
            'artist_url': item['artists'][0]['external_urls']['spotify'],
            'name': item['name'],
            'cover_art': item['album']['images'][0]['url'],
            'album': item['album']['name'],
            'release_date': item['album']['release_date'],
            'duration': convert_duration(item['duration_ms']),
            'song_url': item['external_urls']['spotify'],
            'popularity': item['popularity']
        }

        tracks.append(track)

    return render_template('top_tracks.html', tracks=tracks, enumerate=enumerate)

@app.route('/tracks/recent')
def recently_played():
    sp, redirect_response = get_spotify_client()
    if redirect_response:
        return redirect_response

    try:
        results = sp.current_user_recently_played(limit=50)
    except SpotifyException as e:
        if handle_spotify_exception(e, session['token_info']):
            return recently_played()

    tracks = []

    for item in results['items']:
        track = {
            'artist': item['track']['artists'][0]['name'],
            'artist_url': item['track']['artists'][0]['external_urls']['spotify'],
            'name': item['track']['name'],
            'cover_art': item['track']['album']['images'][0]['url'],
            'song_url': item['track']['external_urls']['spotify'],
            'played_at': parser.parse(item['played_at']).strftime('%d/%m/%y, %H:%M')
        }

        tracks.append(track)

    return render_template('recently_played.html', tracks=tracks, enumerate=enumerate)


if __name__ == "__main__":
    app.run(debug=True)
