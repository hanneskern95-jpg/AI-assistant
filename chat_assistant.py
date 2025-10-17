import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

from tools import spotify_tool


MODEL = "gpt-4o-mini"
MODEL_SEARCH = "gpt-4o-mini"


class assistant:
    load_dotenv(override=True)

    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")
        
    openai = OpenAI()
    system_message = "You are an AI assistant."

    sp_tool = spotify_tool.SpotifyTool(system_prompt = system_message, model = MODEL_SEARCH, openai = openai)
    tools = [{"type": "function", "function": sp_tool.tool}]


    def handle_tools(self, message):
        tool_call = message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        return self.sp_tool.create_spotify_songs(arguments.get("description_playlist"))


    def chat_with_tool(self, message, history):
        history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_message}] + history
        response = self.openai.chat.completions.create(model=MODEL, messages=messages, tools=self.tools)
        
        song_list = None
        if response.choices[0].finish_reason=="tool_calls":
            tool_call = response.choices[0].message.tool_calls[0]
            song_list= self.handle_tools(response.choices[0].message)
            history.append({
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        },
                        "type": tool_call.type
                    }
                ]
            })
            history.append({"role": "assistant", "content": "","type": "function_call_output", "call_id": tool_call.id, "output": song_list})

        response_caught = song_list or response.choices[0].message.content
        history.append({"role":"assistant", "content":response_caught})
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
