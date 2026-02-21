"""
This module defines the `Assistant` class, a conversational agent that integrates with OpenAI's chat API and can call external tools.
It handles the creation of these tools and of specialized sub-Assistants.
"""
from openai import OpenAI

from tool_loader.create import create_tools
from tool_loader.loader import ToolLoader

from .base_assistant import BaseAssistant

MODEL = "gpt-4o-mini"
MODEL_SEARCH = "gpt-4o-mini"


class MasterAssistant(BaseAssistant):
    """A conversational assistant that can call external tools.

    This is simply a thin wrapper around the BaseAssistant that initializes the tool loading and provides a system prompt.
    The main purpose for this class is to handle the cration of tools and avoid circular imports between the base assistant and the tool loading logic.
    The base assistant handles all the core logic of the assistant.

    Attributes:
        system_message (str): System prompt prepended to each request.
        all_tools (dict): Mapping of tool name to tool wrapper instances. It contains all tools any assistant might need.
            The master_chat_asistant itself only uses the tools in the "general" group.
        tool_loader (ToolLoader): An instance of the ToolLoader class that manages tool loading based on groups.
            This allows the creation of sub-Assistants without circular imports.
    """

    def __init__(self) -> None:
        self.system_message = """You are an AI assistant named Thursday.
            You are slightly sarcastic and witty, but always helpful.
            You have access to a set of tools that you can call to get information or perform actions.
            Only call a tool when the user explicitly requests it or when you need it to answer a question that you cannot answer directly.
            Always return the tool's output in your response when you call a tool."""

        self.openai = OpenAI()
        self.all_tools = create_tools(list_of_loaded_groups=["all"], model=MODEL_SEARCH, openai=self.openai)  # type: ignore
        self.tool_loader = ToolLoader(self.all_tools)
        super().__init__(tool_loader=self.tool_loader, list_of_loaded_groups=["general"], system_message=self.system_message, model=MODEL)

