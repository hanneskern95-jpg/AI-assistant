import json
from openai import OpenAI

class Tool():

    tool_dict: dict

    
    def run_tool(self, kwargs) -> str:
        ...
