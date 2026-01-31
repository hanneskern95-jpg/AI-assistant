"""Spotify helper utilities used by the Spotify playlist tool.

This module contains small helpers that interact with the Spotify Web
API via the ``spotipy`` client. Helpers include formatting a song
dictionary into a readable string, searching for a track id, creating
playlists from a list of songs, and fetching the current user's liked
songs from their library.
"""

import os

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv(override=True)


def make_song_string(song_dict: dict) -> str:
    """Format a song dictionary into a single display string.

    Args:
        song_dict (dict): A mapping that contains at least the keys
            ``'name'`` and ``'artist'``.

    Returns:
        str: A string in the form ``"<song name> - <artist>"``.
    """
    return f"{song_dict['name']} - {song_dict['artist']}"


def find_track_id(song_name: str, sp: spotipy.Spotify) -> str | None:
    """Search Spotify for a track and return the first matching id.

    Args:
        song_name (str): Query string used for searching (for example
            the value returned by ``make_song_string``).
        sp (spotipy.Spotify): An authenticated Spotipy client instance.

    Returns:
        str | None: The Spotify track id for the first matching track,
        or ``None`` if no match was found.
    """
    result = sp.search(q=song_name, type="track", limit=10)
    if not result or "tracks" not in result:
        return None
    tracks = result["tracks"]["items"]
    return tracks[0]["id"] if tracks else None


def create_playlist(name: str, song_list: list) -> None:
    """Create a new Spotify playlist for the authenticated user.

    The function authenticates with Spotify (using the embedded
    client id/secret and redirect URI), creates a private playlist
    named ``name``, resolves each provided song to a Spotify track id,
    and adds the tracks to the playlist.

    Args:
        name (str): The desired playlist name.
        song_list (list[dict]): A sequence of song dictionaries with
            at least ``'name'`` and ``'artist'`` keys.

    Returns:
        None

    Raises:
        spotipy.SpotifyException: If playlist creation or item
            addition fails (propagated from the Spotipy client).
    """

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="playlist-modify-public playlist-modify-private",
        )
    )
    me = sp.me()
    if not me:
        raise RuntimeError("Failed to authenticate with Spotify API.")
    user_id = me["id"]

    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description="Created with the Spotify API!",
    )
    if not playlist:
        raise RuntimeError("Failed to create Spotify playlist.")

    ids = [find_track_id(make_song_string(song), sp) for song in song_list]
    sp.playlist_add_items(playlist["id"], ids)


def catch_liked_songs() -> list[str]:
    """Fetch the current user's saved (liked) songs.

    This function paginates through the authenticated user's saved
    tracks and returns a list of readable song strings (``name — artist``).

    Returns:
        list[str]: The user's liked songs as human-readable strings.
    """
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="user-library-read",
        )
    )

    songs = []
    limit = 50
    offset = 0

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        if results is None:
            return []
        items = results["items"]
        if not items:
            break  # no more songs

        for item in items:
            track = item["track"]
            name = track["name"]
            artist = ", ".join([a["name"] for a in track["artists"]])
            songs.append(f"{name} — {artist}")

        offset += limit

    return songs
