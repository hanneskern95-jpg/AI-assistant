import speech_recognition as sr
import streamlit as st
import streamlit_notify as stn

from chat_assistant import Assistant


def switch_input_mode() -> None:
    if st.session_state["input_mode"] == "text":
        st.session_state["input_mode"] = "audio"
    else:
        st.session_state["input_mode"] = "text"


def show_chat() -> None:

    stn.notify()

    #Display chat history
    chat, pinned_object = st.tabs(["Chat", "Pinned Object"])

    with chat:
        placeholder = st.container(height=470, border=False)

        #read prompt
        switch_button_column, input_colum = st.columns([1, 9])
        with switch_button_column:
            with st.container(vertical_alignment="center", height="stretch"):
                st.button(
                    f'{":microphone:" if st.session_state["input_mode"] == "text" else ":keyboard:"}',
                    on_click=switch_input_mode,
                )
        with input_colum:
            if st.session_state["input_mode"] == "text":
                prompt = st.chat_input("Type your message here.")
            else:
                audio_input_column, language_select_column = st.columns([3,1])
                with language_select_column:
                    language = st.selectbox("Language", options=["English", "German", "French", "Spanish"], index=0, key="speech_language")
                    language_tag = {"English": "en-US", "German": "de-DE", "French": "fr-FR", "Spanish": "es-ES"}[language]
                with audio_input_column:
                    prompt_audio = st.audio_input("Press to record")
                    prompt = None
                    if prompt_audio is not None and prompt_audio != st.session_state.get("last_processed_audio", None):
                        recognizer = sr.Recognizer()
                        with sr.AudioFile(prompt_audio) as source:
                            audio = recognizer.record(source)
                        try:
                            prompt = recognizer.recognize_google(audio, language=language_tag) # type: ignore
                        except sr.UnknownValueError:
                            st.warning("Audio not recognized.")
                        except sr.RequestError as e:
                            st.error(f"Speech recognition error: {e}")
                        st.session_state["last_processed_audio"] = prompt_audio
        
        if prompt:
            st.session_state.chat_assistant.chat_with_tool(prompt)

        with placeholder:
            messages_to_display = [message for message in st.session_state.chat_assistant.history if message["role"] in ["user", "assistant", "tool"] and "tool_calls" not in message]
            for message in messages_to_display:
                with st.chat_message(message["role"]):
                    st.session_state.chat_assistant.render_answer(message)

    with pinned_object:
        if st.session_state["pinned_object"] is None:
            st.markdown("No pinned object yet. Pin an object from the chat!")
        else:
            st.session_state.chat_assistant.render_pinned_object(st.session_state["pinned_object"])


if __name__ == "__main__":
    if "chat_assistant" not in st.session_state:
        st.session_state["chat_assistant"] = Assistant()
    if "pinned_object" not in st.session_state:
        st.session_state["pinned_object"] = None
    if "input_mode" not in st.session_state:
        st.session_state["input_mode"] = "text"
    show_chat()
