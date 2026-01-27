"""Spotify playlist creation tool.

This module implements a tool that generates a Spotify playlist based
on a textual description and (optionally) the user's liked songs. The
tool constructs a prompt for the chat model, asks for a JSON-formatted
playlist, and uses helper functions from ``utils.spotify`` to create
the playlist in the user's account.
"""

import json
from typing import TYPE_CHECKING

from openai import OpenAI

from ai_utils import get_response_text_from_chatcompletion

from ...tool import AnswerDict, Tool
from .spotify import catch_liked_songs, create_playlist

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam


class SpotifyTool(Tool):
    """Tool that builds and creates a Spotify playlist.

    The tool assembles a prompt describing the desired playlist,
    optionally includes the user's liked songs as reference, calls the
    chat model to obtain a JSON playlist, and then forwards the result
    to the Spotify helper to create the actual playlist.
    """

    def __init__(self, model: str, openai: OpenAI) -> None:
        """Initialize the SpotifyTool.

        Args:
            model (str): Model identifier used for the chat API.
            openai (OpenAI): An initialized OpenAI client instance.

        Returns:
            None
        """
        self.tool_dict = {
            "type": "function",
            "name": "create_spotify_playlist",
            "description": "Creates a spotify playlist based on a description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description_playlist": {
                        "type": "string",
                        "description": """A description of the desired playlist.The description should contain an overall theme. It can additionally create songs or artists as inspiration.\
                        Example: Search for songs that fit the Theme 'a nice autumn day'. Use the song 'California Dreaming' as inspiration. Use artists similar to 'Green Day' as inspiration.""",
                    },
                    "use_liked_songs": {
                        "type": "boolean",
                        "description": "Whether to use the user's liked songs as a reference when building the playlist.",
                    },
                    "liked_songs_description": {
                        "type": "string",
                        "description": """A string, which descripes how the liked songs should be used to create the playlist. If use_liked_songs is false, this should be empty.\
                        Example 1: The user wishes for a balanced playlist, containing some songs they already like and some new ones, which they do not know already.\
                        Example 2: The user wants a playlist consisting of new songs. Only use the list of liked songs as reference, but do not put already liked songs in the playlist.\
                        Example 3: The user wants a playlist consisting of already liked songs. Exclusively use songs from the list of liked songs.\
                        If no further information on what the user wants is given, use Example 1 as default.""",
                    },
                },
                "required": ["description_playlist"],
                "additionalProperties": False,
            },
        }
        self._system_prompt = "You are an AI assistant helping with creating engaging spotify playlists."
        self._model = model
        self._openai = openai
        self._song_list : str | None = None


    def create_answer(self, song_dict: dict) -> AnswerDict:
        """Render a human-readable answer describing the created playlist.

        Args:
            song_dict (dict): The parsed playlist structure containing
                ``name`` and ``songs``.

        Returns:
            AnswerDict: A dictionary containing a formatted string
            suitable for UI display.
        """
        answer =  f"Created playlist with name '{song_dict['name']}' with the following songs:"
        for song in song_dict["songs"]:
            answer += f"\n{song['name']} - {song.get('artist', '')}"
        return {"answer_str": answer}


    def run_tool(self, *args: object, **kwargs:object) -> AnswerDict:
        """Generate and create a Spotify playlist from the given description.

        The method constructs a chat message asking the model to return
        a JSON playlist (with ``name`` and ``songs``). If
        ``use_liked_songs`` is True the tool will include the user's
        liked songs as context.

        Args:
            description_playlist (str): Text description of the desired playlist.
            use_liked_songs (bool): Whether to include the user's liked songs.
            liked_songs_description (str): How liked songs should be used.

        Returns:
            AnswerDict: The display-ready result after the playlist is created.
        """

        #Validate arguments
        description_playlist = kwargs["description_playlist"]
        use_liked_songs = kwargs.get("use_liked_songs", False)
        liked_songs_description = kwargs.get("liked_songs_description", "")

        assert isinstance(description_playlist, str)
        assert isinstance(use_liked_songs, bool)
        assert isinstance(liked_songs_description, str)

        description_playlist +="""\
        Answer in a json format, containing a title for the playlist and a list of the songs with song name and artist/artists. See the following example:\
        {"name": "Example Playlist", "songs": [{"artist": "example artist_1", "name": "example songname_1"}, {"artist": "example artist_2", "name": "example songname_2"}]}\
        Make the playlist 10 to 20 songs long.
        """

        messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam]

        if use_liked_songs:
            if not self._song_list:
                self._song_list = ", ".join(catch_liked_songs())

            user_message = f"""
            Create a playlist for the user, following the description: {description_playlist}/n
            Use the user's liked songs as reference as follows: {liked_songs_description}/n
            Here is the list of liked songs: {self._song_list}
            """
            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ]
        else:
            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": description_playlist},
            ]

        response = get_response_text_from_chatcompletion(
            self._openai.chat.completions.create(model=self._model, messages=messages, response_format={"type": "json_object"}),
            )
        if response is None:
            return {"answer_str": "Failed to create playlist: No response from model."}
        song_dict = json.loads(response)
        create_playlist(song_dict["name"], song_dict["songs"])
        return self.create_answer(song_dict)
