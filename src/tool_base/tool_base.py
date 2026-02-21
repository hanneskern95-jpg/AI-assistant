"""Tool base classes and registry used by the tools subsystem.

This module defines the `Tool` base class, a simple `AutoRegister`
metaclass that automatically registers concrete tool classes in the
``registry`` list, and a couple of TypedDict shapes used by tool
implementations.
"""

from typing import TypedDict

import streamlit as st
import streamlit_notify as stn

# Registry populated automatically by the AutoRegister metaclass.
registry: list[type] = []


class ToolDict(TypedDict):
    """TypedDict describing a tool's metadata dictionary.

    Fields mirror the small metadata dictionary each tool exposes via
    its ``tool_dict`` attribute and are used when registering tools
    with the OpenAI chat completions API (as function/tool
    descriptions).
    """

    type: str
    name: str
    description: str
    parameters: dict


class AnswerDict(TypedDict):
    """TypedDict representing the minimal answer structure returned by tools."""

    answer_str: str


class Tool:
    """Abstract base class for concrete tool implementations.

    Concrete tool classes should inherit from this base and provide a
    ``tool_dict`` attribute describing the tool and implement
    ``run_tool`` to perform the tool's operation. Subclasses will automatically 
    be put in the list ``registry`` so they can be discovered by `create_tools`.

    All tools belong to a group. The default group is called "general", 
    and is loaded by the chat assistant itself. Child classes of the 
    chat assistant might load different groups.
    """

    tool_dict: ToolDict
    group: str = "general"

    def __init_subclass__(cls, **kwargs: object) -> None:
        registry.append(cls)
        super().__init_subclass__(**kwargs)

    def run_tool(self, *args: object, **kwargs: object) -> AnswerDict:
        """Execute the tool with the provided arguments.

        Subclasses must override this method to perform the tool's
        action and return an ``AnswerDict`` describing the result.

        Args:
            kwargs (dict): Keyword arguments parsed from the model's
                function/tool call payload.

        Returns:
            AnswerDict: A dictionary containing at least ``answer_str``.
        """
        raise NotImplementedError("Subclasses must implement run_tool")

    def render_answer(self, answer: AnswerDict) -> None:
        """Render a tool answer into the Streamlit UI.

        The default implementation renders the ``answer_str`` using
        ``st.markdown``. Tool implementations may override this to
        provide richer rendering.

        Args:
            answer (AnswerDict): The value returned by ``run_tool``.

        Returns:
            None
        """

        st.markdown(answer["answer_str"])

    def render_pinned_object(self, answer: dict) -> None:
        """Render a pinned object stored in session state.

        The default behavior validates the shape and displays the
        ``answer_str``. If the pinned object is malformed an error is
        shown.

        Args:
            answer (dict): Pinned object data produced by this tool.

        Returns:
            None
        """
        if "answer_str" not in answer:
            st.error("Pinned object has invalid format.")
            return
        st.markdown(answer["answer_str"])

    def add_tabbed_object(self, answer: AnswerDict) -> None:
        """Add a pinned object to Streamlit session state and show a toast.

        This helper stores a pinned copy of the tool output in
        ``st.session_state['pinned_object']`` and shows a short toast
        notification to the user.

        Args:
            answer (AnswerDict): The answer object to pin.

        Returns:
            None
        """
        stn.toast("Object pinned!", duration=3, icon="📌")
        st.session_state["pinned_object"] = {
            "function_name": self.tool_dict["name"],
            "AnswerDict": answer,
        }
