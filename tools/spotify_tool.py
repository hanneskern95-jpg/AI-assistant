import json
from .spotify_utils import create_playlist

class SpotifyTool:

    tool = {
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
            },
            "required": ["description_playlist"],
            "additionalProperties": False
        }
    }


    def __init__(self, system_prompt, model, openai):
        self.system_prompt = system_prompt
        self.model = model
        self.openai = openai


    def create_answer(self, song_dict):
        answer =  f"Created PLaylist with name '{song_dict['name']}' with the following songs:"
        for song in song_dict["songs"]:
            answer += f"\n{song['name']} - {song['artist']}"
        return answer
    

    def create_spotify_songs(self, prompt):
        self.system_prompt = "You are an AI assisstant helping with creating engaging spotify playlists."
        prompt +="""\
        Answer in a json format, containing a title for the playlist and a list of the songs with song name and artist/artists. See the following example:\
        {"name": "Example Playlist", "songs": [{"artist": "linkin park", "name": "emptiness machine"}, "{"artist": "breaking benjamin", "name": "diary of jane"}]}\
        Make the playlist 10 to 20 songs long.
        """
        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}]
        response = self.openai.chat.completions.create(model=self.model, messages=messages, response_format={"type": "json_object"})
        song_dict = json.loads(response.choices[0].message.content)
        create_playlist(song_dict["name"], song_dict["songs"])
        return self.create_answer(song_dict)
