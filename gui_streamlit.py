import streamlit as st
from chat_assistant import Assistant


def show_chat() -> None:
    
    #read prompt
    prompt = st.chat_input("Type your message here.")
    if prompt:
        st.session_state.chat_assistant.chat_with_tool(prompt)

    #Display chat history
    messages_to_display = [message for message in st.session_state.chat_assistant.history if message["role"] in ["user", "assistant", "tool"] and "tool_calls" not in message]
    for message in messages_to_display:
        with st.chat_message(message["role"]):
            st.session_state.chat_assistant.render_answer(message)
    print(messages_to_display)


if __name__ == "__main__":
    if "chat_assistant" not in st.session_state:
        st.session_state["chat_assistant"] = Assistant()
    show_chat()
