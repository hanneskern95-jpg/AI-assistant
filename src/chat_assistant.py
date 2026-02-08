"""Assistant module.

This module implements the `Assistant` class which wraps an OpenAI
chat client and a set of tools. It manages conversation history,
dispatches model responses, handles function/tool calls returned by the
model, and renders answers using Streamlit utilities exposed by the
tool implementations.

Dependencies:
    - `openai` for the chat completions API
    - `streamlit` for UI rendering and session state
    - `python-dotenv` for loading environment variables

The file defines the `Assistant` class and module-level constants used
to configure the model.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall
import streamlit as st

from tool_base import AnswerDict
from tools_creator import create_tools

MODEL = "gpt-4o-mini"
MODEL_SEARCH = "gpt-4o-mini"


class Assistant:
    """A conversational assistant that can call external tools.

    The `Assistant` encapsulates an OpenAI chat client and a collection
    of tool wrappers. It maintains a conversation history compatible
    with OpenAI's chat API, detects tool/function calls returned by
    the model, executes the corresponding tool, and appends tool
    outputs back into the history for subsequent messages.

    Attributes:
        openai_api_key (str | None): API key read from the environment.
        openai (OpenAI): OpenAI client instance.
        system_message (str): System prompt prepended to each request.
        tools (dict): Mapping of tool name to tool wrapper instances.
        tool_dicts (list): Tool metadata used when calling the model.
        history (list[dict]): Conversation history as a list of message
            dicts compatible with the chat API.
    """

    load_dotenv(override=True)

    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("OpenAI API Key not set")

        self.openai = OpenAI()
        self.system_message = "You are an AI assistant."

        self.tools = create_tools(model=MODEL_SEARCH, openai=self.openai)  # type: ignore
        self.tool_dicts = [{"type": "function", "function": tool.tool_dict} for tool in self.tools.values()]
        self.history: list[dict] = []

    def get_attributes_from_tool_call_message(self, message: ChatCompletionMessage) -> tuple[ChatCompletionMessageFunctionToolCall | None, str, dict, str]:
        """Extract tool call attributes from a model message.

        The OpenAI response message may contain one or more tool/function
        calls. This helper validates that a tool call exists and returns
        a tuple with the parsed attributes required to execute the tool.

        Args:
            message (ChatCompletionMessage): The model message potentially
                containing a tool call.

        Returns:
            tuple[ChatCompletionMessageFunctionToolCall | None, str, dict, str]:
                A 4-tuple containing the raw tool call object (or ``None``
                when absent), the function name (or empty string), the
                parsed arguments as a dict (or empty dict), and the raw
                arguments JSON string (or empty string).
        """
        if not message.tool_calls:
            st.error("No tool call found in the message.")
            return None, "", {}, ""

        tool_call = message.tool_calls[0]
        if not hasattr(tool_call, "function") or not tool_call.function:  # type: ignore
            st.error("No tool call found in the message.")
            return None, "", {}, ""

        arguments_str = tool_call.function.arguments  # type: ignore
        return tool_call, tool_call.function.name, json.loads(arguments_str), arguments_str  # type: ignore

    def handle_tools(self, message: ChatCompletionMessage) -> AnswerDict:
        """Execute a tool call returned by the model and append results.

        This method extracts the first tool call from `message`, records
        the tool call metadata into the assistant's history, invokes the
        corresponding tool implementation with the parsed arguments,
        then appends the tool's response to the history.

        Args:
            message (ChatCompletionMessage): Model message containing a
                function/tool call.

        Returns:
            AnswerDict: The dictionary returned by the executed tool. If
            no tool call is present an error-like AnswerDict is
            returned.
        """
        tool_call, function_name, arguments, arguments_str = self.get_attributes_from_tool_call_message(message)
        if tool_call is None:
            return {"answer_str": "Error: No tool call found."}

        self.history.append(
            {
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
            }
        )

        tool_answer = self.tools[function_name].run_tool(**arguments)
        self.history.append({"role": "tool", "content": "", "tool_answer": tool_answer, "tool_name": function_name, "tool_call_id": tool_call.id})
        return tool_answer

    def chat_with_tool(self, message: ChatCompletionMessage) -> None:
        """Send the user message to the model, handle tools, and update history.

        The provided `message` is appended to the internal history and the
        assistant calls the OpenAI chat completions API with the system
        prompt and accumulated conversation. If the model triggers a
        tool/function call the tool is executed and its result appended
        to history; otherwise the assistant's textual reply is appended.

        Args:
            message (ChatCompletionMessage): The user's message content to
                include in the conversation.

        Returns:
            None: The function updates the conversation history in-place.
        """
        # Append the user message to the shared history attribute
        self.history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_message}, *self.history]
        response = self.openai.chat.completions.create(model=MODEL, messages=messages, tools=self.tool_dicts)  # type: ignore

        if response.choices[0].finish_reason == "tool_calls":
            self.handle_tools(response.choices[0].message)
        else:
            self.history.append({"role": "assistant", "content": response.choices[0].message.content})

    def render_answer(self, message: dict) -> None:
        """Render a chat message to the Streamlit UI.

        Depending on the message role this will either render plain text
        (for assistant/user roles) or delegate rendering to the tool
        implementation (for tool role messages).

        Args:
            message (dict): A message dictionary from `self.history` with
                at least a ``role`` key. Tool messages are expected to
                include ``tool_name`` and ``tool_answer`` keys.

        Returns:
            None
        """
        if message["role"] in ("assistant", "user"):
            st.markdown(message["content"])
        if message["role"] == "tool":
            tool = self.tools[message["tool_name"]]
            tool.render_answer(message["tool_answer"])

    def render_pinned_object(self, pinned_object: dict) -> None:
        """Render a pinned object using the originating tool's renderer.

        Args:
            pinned_object (dict): A pinned object structure containing at
                minimum ``function_name`` and ``AnswerDict`` keys produced
                by a previous tool call.

        Returns:
            None
        """
        tool = self.tools[pinned_object["function_name"]]
        tool.render_pinned_object(pinned_object["AnswerDict"])
