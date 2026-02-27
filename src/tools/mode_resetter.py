"""Mail mode switcher tool.

This tool creates a MailAssistant instance and adds it to Streamlit's st.session_state.
"""

import streamlit as st

from tool_base import AnswerDict, Tool


class ModeSwitcherDict(AnswerDict):
    is_mode_switcher: bool
    switches_to: str
    carry_over_tool_calls: bool
    summary_previous_tool: str

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
                "properties": {
                    "summary_previous_tool": {
                        "type": "string",
                        "description": """A brief summary of the conversaton the previous tool had with the user, to help the master assistant pick up the conversation.
                            This should be a concise summary of the main points covered in the conversation, any important information provided by the user, and any 
                            outstanding questions or issues that the master assistant should be aware of when taking over the conversation.
                            Summarize everything that happend since the last time a 'mode_switcher' tool was called, or since the beginning of the conversation if no 
                            'mode_switcher' tool was called yet. A mode_switcher tool shopuld have mode_switcher in its name and  a flag 'is_mode_switcher' set to True in its 
                            return dict called 'tool_answer'. 
                            The summary should be no more than a few sentences long and should capture the essence of the conversation without going into too much detail.""",
                    },
                },
                "required": ["summary_previous_tool"],
            },
        }

    def run_tool(self, *args: object, **kwargs: object) -> ModeSwitcherDict:
        st.session_state["chat_assistant"].close()
        st.session_state["chat_assistant"] = st.session_state["master_assistant"]
        return {
            "answer_str": "Switched back to standard assistant.",
            "is_mode_switcher": True, # this flag can be used by the frontend to know that the mode was switched and maybe display the summary of the previous conversation or do other UI updates.
            "switches_to": "master_assistant",
            "carry_over_tool_calls": True, # this flag indicates that the tool calls from the previous conversation should be carried over to the new assistant.
            "summary_previous_tool": str(kwargs.get("summary_previous_tool", "")),
        }