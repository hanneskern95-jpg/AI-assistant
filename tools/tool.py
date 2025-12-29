from typing import Any, TypedDict

import streamlit as st
import streamlit_notify as stn

registry = []


class AutoRegister(type):
    def __init__(cls, name: str, bases: tuple, attrs: dict[str, Any]) -> None:
        if name != "Tool":
            registry.append(cls)
        super().__init__(name, bases, attrs)


class ToolDict(TypedDict):
    type: str
    name: str
    description: str
    parameters: dict


class AnswerDict(TypedDict):
    answer_str: str


class Tool(metaclass=AutoRegister):

    tool_dict: ToolDict


    def run_tool(self, kwargs: dict) -> AnswerDict:
        raise NotImplementedError("Subclasses must implement run_tool")
        
    
    def render_answer(self, answer: AnswerDict) -> None:
        st.markdown(answer["answer_str"])


    def render_pinned_object(self, answer: dict) -> None:
        if "answer_str" not in answer:
            st.error("Pinned object has invalid format.")
            return
        st.markdown(answer["answer_str"])


    def add_tabbed_object(self, answer: AnswerDict) -> None:
        stn.toast("Recipe pinned!", duration=3, icon="📌")
        st.session_state["pinned_object"] = {
            "function_name": self.tool_dict["name"],
            "AnswerDict": answer,
        }