import json
import os

from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import streamlit as st

from tools import create_tools

MODEL = "gpt-4o-mini"
MODEL_SEARCH = "gpt-4o-mini"


class Assistant:
    load_dotenv(override=True)

    def __init__(self) -> None:
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            print(f"OpenAI API Key exists and begins {self.openai_api_key[:8]}")
        else:
            print("OpenAI API Key not set")
            
        self.openai = OpenAI()
        self.system_message = "You are an AI assistant."

        self.tools = create_tools(model = MODEL_SEARCH, openai = self.openai)
        print(self.tools)
        self.tool_dicts = [{"type": "function", "function": tool.tool_dict} for tool in self.tools.values()]
        # Conversation history stored as an attribute on the Assistant instance
        # It's a list of OpenAI-style message dicts: {"role": ..., "content": ...}
        self.history: list[dict] = []


    def handle_tools(self, message):
        """Handle a tool call contained in `message` and update self.history.

        The method reads the first tool call, appends the tool call metadata to
        history, runs the tool, then appends the tool output to history.
        """
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments_str = tool_call.function.arguments
        arguments = json.loads(arguments_str)

        self.history.append({
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "function": {
                            "name": function_name,
                            "arguments": arguments_str,
                        },
                        "type": tool_call.type,
                    },
                ],
        })

        tool_answer = self.tools[function_name].run_tool(**arguments)
        self.history.append({"role": "tool", "content": "", "tool_answer": tool_answer, "tool_name": function_name, "tool_call_id": tool_call.id})
        return tool_answer


    def chat_with_tool(self, message):
        """Receive a user message, call the model (and tools if needed),
        and update self.history. Returns values to update the Gradio UI:
        (cleared_input, updated_chatbot_value).
        """
        # Append the user message to the shared history attribute
        self.history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_message}, *self.history]
        response = self.openai.chat.completions.create(model=MODEL, messages=messages, tools=self.tool_dicts)

        if response.choices[0].finish_reason == "tool_calls":
            self.handle_tools(response.choices[0].message)
        else:
            self.history.append({"role": "assistant", "content": response.choices[0].message.content})

        # Return an empty string to clear the entry textbox and the history list
        # to update the Chatbot component in the UI
        return "", self.history


    def render_answer(self, message: dict) -> None:
        if message["role"] in ("assistant", "user"):
            st.markdown(message["content"])
        if message["role"] == "tool":
            tool = self.tools[message["tool_name"]]
            tool.render_answer(message["tool_answer"])


    def start_chat_assistant(self) -> None:
        with gr.Blocks() as ui:
            with gr.Row():
                # Initialize the Chatbot's displayed value from self.history
                chatbot = gr.Chatbot(value=self.history, height=500)
            with gr.Row():
                entry = gr.Textbox(label="Chat with our AI Assistant:")
            # Only pass the Textbox input to the function; the function uses
            # self.history internally and returns it as the Chatbot output.
            entry.submit(self.chat_with_tool, inputs=[entry], outputs=[entry, chatbot])

        ui.launch(inbrowser=True)

    
if __name__ == '__main__':

    chat_assistant = Assistant()
    chat_assistant.start_chat_assistant()
