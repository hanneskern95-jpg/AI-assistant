"""Streamlit GUI for the Chat Assistant.

This module provides the Streamlit-based user interface used to interact
with the `Assistant` object. It supports text and audio input modes and
renders the chat history and a pinned object panel.

The UI leverages `speech_recognition` for audio transcription and
`streamlit_notify` for notifications.
"""

import speech_recognition as sr
import streamlit as st
import streamlit_notify as stn

from chat_assistant.master_chat_assistant import MasterAssistant


def _switch_input_mode() -> None:
    """Toggle the Streamlit input mode between text and audio.

    This function flips the value of `st.session_state["input_mode"]`
    between the strings ``"text"`` and ``"audio"``. It is intended to
    be used as a callback for UI controls (for example a button) so the
    user can switch how they provide prompts to the assistant.

    Returns:
        None: The function updates Streamlit session state in-place.
    """
    if st.session_state["input_mode"] == "text":
        st.session_state["input_mode"] = "audio"
    else:
        st.session_state["input_mode"] = "text"


def _get_audio_input(language_tag: str) -> str | None:
    """Capture and transcribe audio input from the Streamlit UI.

    This helper reads a new audio recording from `st.audio_input`, avoids
    re-processing the same audio twice by comparing against
    `st.session_state["last_processed_audio"]`, and then uses the
    Google Speech Recognition backend (via `speech_recognition`) to
    transcribe the audio to text.

    Args:
        language_tag (str): Language code passed to the recognizer
            (for example ``"en-US"`` or ``"de-DE"``).

    Returns:
        str | None: The transcribed text on success; ``None`` if there is
        no new audio, the audio could not be recognized, or a
        recognition error occurred.
    """
    prompt_audio = st.audio_input("Press to record")
    if prompt_audio is not None and prompt_audio != st.session_state.get("last_processed_audio", None):
        st.session_state["last_processed_audio"] = prompt_audio
        recognizer = sr.Recognizer()
        with sr.AudioFile(prompt_audio) as source:
            audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio, language=language_tag)  # type: ignore
        except sr.UnknownValueError:
            st.warning("Audio not recognized.")
            return None
        except sr.RequestError as e:
            st.error(f"Speech recognition error: {e}")
            return None
    return None


def show_chat() -> None:
    """Render the chat UI and handle user interactions.

    This function composes the Streamlit interface for the assistant. It
    creates two tabs: one for the chat conversation and one for a pinned
    object. The chat tab shows the message history, provides a control
    to switch between text and audio input modes, and dispatches user
    input to the `Assistant` via
    ``st.session_state.chat_assistant.chat_with_tool``.

    The pinned object tab displays a currently pinned object (if any)
    using ``st.session_state.chat_assistant.render_pinned_object``.

    Returns:
        None: UI is rendered directly to the active Streamlit app.
    """

    stn.notify()
    chat, pinned_object = st.tabs(["Chat", "Pinned Object"])

    with chat:
        placeholder = st.container(height=470, border=False)

        # read prompt
        switch_button_column, input_colum = st.columns([1, 9])
        with switch_button_column:
            with st.container(vertical_alignment="center", height="stretch"):
                st.button(
                    f"{':microphone:' if st.session_state['input_mode'] == 'text' else ':keyboard:'}",
                    on_click=_switch_input_mode,
                )
        with input_colum:
            if st.session_state["input_mode"] == "text":
                prompt = st.chat_input("Type your message here.")
            else:
                audio_input_column, language_select_column = st.columns([3, 1])
                with language_select_column:
                    language = st.selectbox("Language", options=["English", "German", "French", "Spanish"], index=0, key="speech_language")
                    language_tag = {"English": "en-US", "German": "de-DE", "French": "fr-FR", "Spanish": "es-ES"}[language]
                with audio_input_column:
                    prompt = _get_audio_input(language_tag)

        if prompt:
            st.session_state["full_history"].extend(st.session_state.chat_assistant.chat_with_tool(prompt))

        with placeholder:
            messages_to_display = [message for message in st.session_state.full_history if message["role"] in ["user", "assistant", "tool"] and "tool_calls" not in message]
            for message in messages_to_display:
                with st.chat_message(message["role"]):
                    if message["role"] in ("assistant", "user"):
                        st.markdown(message["content"])
                    if message["role"] == "tool":
                        tool = st.session_state["tools"][message["tool_name"]]
                        tool.render_answer(message["tool_answer"])

    with pinned_object:
        if st.session_state["pinned_object"] is None:
            st.markdown("No pinned object yet. Pin an object from the chat!")
        else:
            pinned_object = st.session_state["pinned_object"]
            tool = st.session_state["tools"][pinned_object["function_name"]]
            tool.render_pinned_object(pinned_object["AnswerDict"])


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables.

    This function sets up the necessary session state variables for the
    chat assistant application. It creates a `MasterAssistant` instance
    and stores it under both `chat_assistant` and `master_assistant`
    keys, initializes an empty list for `full_history`, sets
    `pinned_object` to `None`, and defaults `input_mode` to `"text"`.

    Returns:
        None: Session state is modified in-place.
    """
    if "tools" not in st.session_state:
        st.session_state["tools"] = {}
    if "chat_assistant" not in st.session_state:
        master_assistant = MasterAssistant()
        st.session_state["chat_assistant"] = master_assistant
        st.session_state["master_assistant"] = master_assistant
    if "pinned_object" not in st.session_state:
        st.session_state["pinned_object"] = None
    if "full_history" not in st.session_state:
        st.session_state["full_history"] = []
    if "input_mode" not in st.session_state:
        st.session_state["input_mode"] = "text"

if __name__ == "__main__":
    initialize_session_state()
    show_chat()
