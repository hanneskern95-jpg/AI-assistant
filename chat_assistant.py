import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall
import streamlit as st

from tools import AnswerDict, create_tools

MODEL = "gpt-4o-mini"
MODEL_SEARCH = "gpt-4o-mini"


class Assistant:
    load_dotenv(override=True)

    def __init__(self) -> None:
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            print("OpenAI API Key not set")
            
        self.openai = OpenAI()
        self.system_message = "You are an AI assistant."

        self.tools = create_tools(model = MODEL_SEARCH, openai = self.openai) # type: ignore
        self.tool_dicts = [{"type": "function", "function": tool.tool_dict} for tool in self.tools.values()]
        # Conversation history stored as an attribute on the Assistant instance
        # It's a list of OpenAI-style message dicts: {"role": ..., "content": ...}
        self.history: list[dict] = []


    def get_attributes_from_tool_call_message(self, message: ChatCompletionMessage) -> tuple[ChatCompletionMessageFunctionToolCall | None, str, dict, str]:
        if not message.tool_calls:
            st.error("No tool call found in the message.")
            return None, "", {}, ""
        
        tool_call = message.tool_calls[0]
        if not hasattr(tool_call, 'function') or not tool_call.function: # type: ignore
            st.error("No tool call found in the message.")
            return None, "", {}, ""
        
        arguments_str = tool_call.function.arguments # type: ignore
        return tool_call, tool_call.function.name, json.loads(arguments_str), arguments_str # type: ignore


    def handle_tools(self, message: ChatCompletionMessage) -> AnswerDict:
        """Handle a tool call contained in `message` and update self.history.

        The method reads the first tool call, appends the tool call metadata to
        history, runs the tool, then appends the tool output to history.
        """
        tool_call, function_name, arguments, arguments_str = self.get_attributes_from_tool_call_message(message)
        if tool_call is None:
            return {"answer_str": "Error: No tool call found."}
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


    def chat_with_tool(self, message: ChatCompletionMessage) -> tuple[str, list[dict]]:
        """Receive a user message, call the model (and tools if needed),
        and update self.history. Returns values to update the Gradio UI:
        (cleared_input, updated_chatbot_value).
        """
        # Append the user message to the shared history attribute
        self.history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_message}, *self.history]
        response = self.openai.chat.completions.create(model=MODEL, messages=messages, tools=self.tool_dicts)  # type: ignore

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

    
    def render_pinned_object(self, pinned_object: dict) -> None:
        tool = self.tools[pinned_object["function_name"]]
        tool.render_pinned_object(pinned_object["AnswerDict"])
