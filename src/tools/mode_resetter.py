"""Mail mode switcher tool.

This tool creates a MailAssistant instance and adds it to Streamlit's st.session_state.
"""

import streamlit as st

from tool_base import AnswerDict, Tool


class ModeResetter(Tool):
    """
    Switches back to the master assistant mode.
    """
    group = "sub_assistant"

    def __init__(self) -> None:
        self.tool_dict = {
            "type": "function",
            "name": "switch_back_to_master_mode",
            "description": "Switches back to the master assistant mode. The user might also call the master mode 'standard assistant'",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

    def run_tool(self, *args: object, **kwargs: object) -> AnswerDict:
        st.session_state["chat_assistant"] = st.session_state["master_assistant"]
        return {"answer_str": "Switched back to standard assistant."}