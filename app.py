import uuid
import time
import re
import streamlit as st
from datetime import datetime
from agent.utils.diagram_helper import generate
from agent.agent import invoke 
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


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

if "state_messages" not in st.session_state:
    st.session_state.state_messages = []

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

    message = st.chat_input("What is up?")
    if message:
        response, image_path, python_diagram_code, messages = invoke(message=message, thread_id=st.session_state.chat_id)
        st.session_state.state_messages = messages
        
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


tab1, tab2, tab3, tab4 = st.tabs(["Diagram", "Python Diagram Code", "Agent Graph", "Agent Reasoning"])

with tab1:
    try:
        st.image(st.session_state.image_path)
        # Add download button for the diagram image
        if st.session_state.image_path:
            with open(st.session_state.image_path, "rb") as img_file:
                with st.container(horizontal=True, horizontal_alignment="right"):
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
    st.image("static/agent_graph.png", caption="Agent")

with tab4:
    formatted_messages = []
    for message in st.session_state.state_messages:        
        message_type = type(message)
        if message_type == HumanMessage:
            message_type = "Human"
            message_content = message.content if hasattr(message, 'content') else str(message)
        elif message_type == AIMessage:
            message_type = "AI"
            response_metadata = message.response_metadata if hasattr(message, 'response_metadata') else  None
            if response_metadata:
                message_content = ""
                if "step" in response_metadata:
                    message_content += f"\n\n     Step: {response_metadata['step']}"
                if "error_messages" in response_metadata:
                    error_msgs = response_metadata["error_messages"]
                    if isinstance(error_msgs, list):
                        error_msgs = "\n".join([f"- {err}" for err in error_msgs])
                    message_content += f"\n\n     Error Messages:\n{error_msgs}"
                if "documentation_snippets" in response_metadata:
                    doc_snippets = response_metadata["documentation_snippets"]
                    if isinstance(doc_snippets, list):
                        doc_snippets = "\n".join([f"- {snippet}" for snippet in doc_snippets])
                    message_content += f"\n\n     Documentation Snippets:\n{doc_snippets}"
                if "python_diagram_code" in response_metadata:
                    python_code = response_metadata["python_diagram_code"]
                    if python_code:
                        message_content += f"\n\n     Python Diagram Code:\n```python\n{python_code}\n```"
            else:
                message_content = message.content if hasattr(message, 'content') else str(message)
        elif message_type == SystemMessage:
            message_type = "System"
        
        formatted_message = f"**{message_type}:** {message_content}"
        formatted_messages.append(formatted_message)
    st.markdown("\n\n".join(formatted_messages))