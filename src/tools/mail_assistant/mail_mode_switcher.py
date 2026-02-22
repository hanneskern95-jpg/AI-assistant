"""Mail mode switcher tool.

This tool creates a MailAssistant instance and adds it to Streamlit's st.session_state.
"""

import streamlit as st

from tool_base import AnswerDict, Tool
from tool_loader.loader import ToolLoader

from .mail_assistant import MailAssistant


class MailModeSwitcher(Tool):
    """
    Tool to switch to mail mode by creating a MailAssistant and storing it in session state.
    """

    def __init__(self, tool_loader: ToolLoader) -> None:
        self.tool_dict = {
            "type": "function",
            "name": "switch_to_mail_mode",
            "description": "Switches the assistant to mail mode by creating a MailAssistant and storing it in Streamlit session state.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
        self.tool_loader = tool_loader

    def run_tool(self, *args: object, **kwargs: object) -> AnswerDict:
        if "mail_assistant" not in st.session_state:
            st.session_state["mail_assistant"] = MailAssistant(tool_loader=self.tool_loader)
        st.session_state["chat_assistant"] = st.session_state["mail_assistant"]
        return {"answer_str": "Switched to mail mode. MailAssistant is now active."}
