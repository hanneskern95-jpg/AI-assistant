import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json


def make_song_string(song_dict):
    return f"{song_dict['name']} - {song_dict['artist']}"


def find_track_id(song_name, sp):
    result = sp.search(q=song_name, type="track", limit=10)
    tracks = result["tracks"]["items"]
    return tracks[0]["id"] if tracks else None


def create_playlist(name, song_list):

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id="db283fe46ff3452ebeecfc328a68fb58",
        client_secret="28d8a27fca2440319df77c97ae50e22e",
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="playlist-modify-public playlist-modify-private"
    ))

    user_id = sp.me()["id"]

    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description="Created with the Spotify API!"
    )

    ids = [find_track_id(make_song_string(song), sp) for song in song_list]

    sp.playlist_add_items(playlist["id"], ids)
