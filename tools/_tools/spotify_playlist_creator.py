import json
from ..utils.spotify import create_playlist, catch_liked_songs
from ..tool import Tool, AnswerDict

class SpotifyTool(Tool):

    def __init__(self, model, openai):
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
                        "description": "Decides if the creator of the playlist should use the user's liked songs as a reference. If not stated explicitly, set this to true as default. If the user asks for a 'general' or 'generic' playlist, set this to false."
                    },
                    "liked_songs_description": {
                        "type": "string",
                        "description": """A string, which descripes how the liked songs should be used to create the playlist. If use_liked_songs is false, this should be empty.\
                        Example 1: The user wishes for a balanced playlist, containing some songs they already like and some new ones, which they do not know already.\
                        Example 2: The user wants a playlist consisting of new songs. Only use the list of liked songs as reference, but do not put already liked songs in the playlist.\
                        Example 3: The user wants a playlist consisting of already liked songs. Exclusively use songs from the list of liked songs.\
                        If no further information on what the user wants is given, use Example 1 as default.""",
                    }
                },
                "required": ["description_playlist"],
                "additionalProperties": False
            }
        }
        self._system_prompt = "You are an AI assisstant helping with creating engaging spotify playlists."
        self._model = model
        self._openai = openai
        self._song_list = None


    def create_answer(self, song_dict) -> AnswerDict:
        answer =  f"Created PLaylist with name '{song_dict['name']}' with the following songs:"
        for song in song_dict["songs"]:
            answer += f"\n{song['name']} - {song['artist']}"
        return {"answer_str": answer}


    def run_tool(self, description_playlist, use_liked_songs = False, liked_songs_description = ""):

        description_playlist +="""\
        Answer in a json format, containing a title for the playlist and a list of the songs with song name and artist/artists. See the following example:\
        {"name": "Example Playlist", "songs": [{"artist": "linkin park", "name": "emptiness machine"}, "{"artist": "breaking benjamin", "name": "diary of jane"}]}\
        Make the playlist 10 to 20 songs long.
        """

        if use_liked_songs:
            if not self._song_list:
                self._song_list = ", ".join(catch_liked_songs())
            messages = [{"role": "system", "content": self._system_prompt}, {"role": "system", "content": "Here is a list of the user's liked songs. "+self._song_list}, {"role": "system", "content": liked_songs_description},{"role": "user", "content": description_playlist}]
        else:
            messages = [{"role": "system", "content": self._system_prompt}, {"role": "user", "content": description_playlist}]

        response = self._openai.chat.completions.create(model=self._model, messages=messages, response_format={"type": "json_object"})
        song_dict = json.loads(response.choices[0].message.content)
        create_playlist(song_dict["name"], song_dict["songs"])
        return self.create_answer(song_dict)
