import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

from tools.tools.spotify_playlist_creator import SpotifyTool


MODEL = "gpt-4o-mini"
MODEL_SEARCH = "gpt-4o-mini"


class assistant:
    load_dotenv(override=True)

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            print(f"OpenAI API Key exists and begins {self.openai_api_key[:8]}")
        else:
            print("OpenAI API Key not set")
            
        self.openai = OpenAI()
        self.system_message = "You are an AI assistant."

        self.tools = {
            "create_spotify_playlist": SpotifyTool(MODEL_SEARCH, self.openai)
        }
        self.tool_dicts = [{"type": "function", "function": tool.tool_dict} for tool in self.tools.values()]


    def handle_tools(self, message, history):
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        history.append({
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "function": {
                            "name": function_name,
                            "arguments": arguments
                        },
                        "type": tool_call.type
                    }
                ]
        })

        tool_answer = self.tools[function_name].run_tool(**arguments)
        history.append({"role": "assistant", "content": tool_answer,"type": "function_call_output", "call_id": tool_call.id, "output": tool_answer})

        return tool_answer


    def chat_with_tool(self, message, history):
        history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_message}] + history
        response = self.openai.chat.completions.create(model=MODEL, messages=messages, tools=self.tool_dicts)
        
        if response.choices[0].finish_reason=="tool_calls":
            answer = self.handle_tools(response.choices[0].message, history)
        else:
            history.append({"role":"assistant", "content":response.choices[0].message.content})

        return "", history


    def start_chat_assistant(self):
        with gr.Blocks() as ui:
            with gr.Row():
                chatbot = gr.Chatbot(height=500, type="messages")
            with gr.Row():
                entry = gr.Textbox(label="Chat with our AI Assistant:")
            entry.submit(self.chat_with_tool, inputs=[entry, chatbot], outputs=[entry, chatbot])

        ui.launch(inbrowser=True)
    
if __name__ == '__main__':

    chat_assistant = assistant()
    chat_assistant.start_chat_assistant()
