import streamlit as st
from chat_assistant import Assistant


def show_chat() -> None:
    
    #read prompt
    prompt = st.chat_input("Type your message here.")
    if prompt:
        st.session_state.chat_assistant.chat_with_tool(prompt)

    #Display chat history
    chat, pinned_object = st.tabs(["Chat", "Pinned Object"])

    with chat:
        with st.container(height=470, border=False):
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
    show_chat()
