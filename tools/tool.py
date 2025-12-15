import streamlit as st
from typing import TypedDict


registry = []


class AutoRegister(type):
    def __init__(cls, name, bases, attrs):
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


    def run_tool(self, kwargs) -> AnswerDict:
        raise NotImplementedError("Subclasses must implement run_tool")
        
    
    def render_answer(self, answer: AnswerDict) -> None:
        st.markdown(answer["answer_str"])


    def render_pinned_object(self, answer: AnswerDict) -> None:
        st.markdown(answer["answer_str"])
