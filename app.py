import uuid
import streamlit as st
from agent.utils.diagram_handler import generate

st.set_page_config(layout="wide")

if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = ["Chat 1","Chat 2","Chat 3"]

with st.sidebar:
    chatbot = st.selectbox("Chat history",
                           st.session_state.chat_history,
                           index=None,
                           placeholder="Start to chat or select previous chat")

    # Display chat messages from history on app rerun
    with st.container(height=400):
        for message in st.session_state.messages:
            with st.chat_message(name=message["role"]):
                st.markdown(message["content"])

    if message := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": message})
        st.session_state.messages.append({"role": "assistant", "content": message})
        st.rerun()

generate()
st.image("./output/diagram_image.png") 