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


class Tool(metaclass=AutoRegister):

    tool_dict: ToolDict


    def run_tool(self, kwargs) -> dict:
        raise NotImplementedError("Subclasses must implement run_tool")
        
    
    def render_answer(self, answer: dict) -> None:
        st.markdown(answer["content_str"])
