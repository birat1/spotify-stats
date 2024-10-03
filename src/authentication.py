import os
from flask import redirect, session, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope='user-read-recently-played user-top-read'
    )

def get_spotify_client():
    # Get token info from session
    token_info = session.get("token_info", None)
    # If token info is not found, redirect to login
    if not token_info:
        return None, redirect(url_for('login'))

    sp_oauth = get_spotify_oauth()
    # If token is expired, refresh it
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        # Update token info in session
        session['token_info'] = token_info
  
    return Spotify(auth=token_info['access_token']), None

def handle_spotify_exception(e, token_info):
    sp_oauth = get_spotify_oauth()
    # If unauthorized, refresh token
    if e.http_status == 401:
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
        return True
    raise e