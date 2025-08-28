import uuid
import time
import streamlit as st
from datetime import datetime
from agent.utils.diagram_helper import generate
from agent.agent import invoke 
#st.set_page_config(layout="wide")


def display_past_values(image_path, python_diagram_code):
    st.session_state.image_path = image_path
    st.session_state.python_diagram_code = python_diagram_code

if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "image_path" not in st.session_state:
    st.session_state.image_path = None

if "python_diagram_code" not in st.session_state:
    st.session_state.python_diagram_code = ""

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
                if message["role"] == "assistant":
                    if message["metadata"].get("image_path") and message["metadata"].get("python_diagram_code"):
                        key = str(uuid.uuid4())
                        st.button(f"Generated Diagram 🖼️", 
                                type="primary",
                                key=key,
                                on_click=display_past_values,
                                args=(message["metadata"].get("image_path"), message["metadata"].get("python_diagram_code"))
                                )

    if message := st.chat_input("What is up?"):
        response, image_path, python_diagram_code = invoke(message=message, thread_id=st.session_state.chat_id)
        metadata = {}
        if image_path != st.session_state.image_path:
            metadata["image_path"] = image_path
        else:
            metadata["image_path"] = None
        if python_diagram_code != st.session_state.python_diagram_code:
            metadata["python_diagram_code"] = python_diagram_code
        else:
            metadata["python_diagram_code"] = None

        st.session_state.messages.append({"role": "user", "content": message})
        st.session_state.messages.append({"role": "assistant", "content": response, "metadata": metadata})
        st.session_state.image_path = image_path
        st.session_state.python_diagram_code = python_diagram_code
        st.rerun()


tab1, tab2, tab3 = st.tabs(["Diagram", "Python Diagram Code", "Agent Graph"])

with tab1:
    try:
        st.image(st.session_state.image_path)
        # Add download button for the diagram image
        if st.session_state.image_path:
            with open(st.session_state.image_path, "rb") as img_file:
                st.download_button(
                    label="Download Diagram Image",
                    data=img_file,
                    file_name="diagram.png",
                    mime="image/png"
                )
    except:
        pass

with tab2:
    st.code(st.session_state.python_diagram_code)

with tab3:
    st.image("agent.png", caption="Agent")
