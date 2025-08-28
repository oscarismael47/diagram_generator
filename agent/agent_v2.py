import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import MessagesState
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
try:
    from agent.utils.diagram_helper import generate, check_modules
    from agent.utils.qdrant_helper import QdrantHandler
except:
    from utils.diagram_helper import generate, check_modules
    from utils.qdrant_helper import QdrantHandler
load_dotenv()


MODEL = st.secrets.get("OPENAI_MODEL")
API_KEY = st.secrets.get("OPENAI_KEY")
EMBEDDING_MODEL = st.secrets.get("OPENAI_EMBEDDING_MODEL")
EMBEDDING_SIZE = st.secrets.get("OPENAI_EMBEDDING_SIZE")

# Initialize the OpenAI model with the API key and model name from Streamlit secrets
#MODEL = os.getenv("OPENAI_MODEL")
#API_KEY = os.getenv("OPENAI_KEY")

class DiagramData(BaseModel):
    """
    Data model for storing diagram generation information.

    Attributes:
        import_code (str): The import statements required for the diagram.
        diagram_code (str): The code that defines the diagram structure.
        ai_response (str): The AI-generated response or explanation.
    """
    import_code: str = Field(..., description="The import statements required for the diagram.")
    diagram_code: str = Field(..., description="The code that defines the diagram structure.")
    ai_response: str = Field(..., description="The AI-generated response or explanation.")

class State(MessagesState):
    import_code: str
    diagram_code: str
    python_diagram_code: str
    image_path: str
    error_messages: list[str]

def assistant(state: State):
    MODEL_SYSTEM_MESSAGE = """
    You are a helpful assistant that generates diagrams based on user input.

    Your responsibilities:
    1. Answer the user’s questions in a clear, concise, and friendly way.  
    2. Ask clarifying questions about the user’s preferences or requirements when needed.  
    3. Generate the correct `import_code` and `diagram_code` (Python code using the diagrams library) based strictly on the user’s input.  
    4. Revise and improve the diagram when the user provides feedback.
    5. If the diagram was generated successfully, notify the user, and add a diagram description.

    Output format:  
    Always return three fields:
    - import_code → contains only the necessary Python imports.  Do not include any comments, only python code
    - diagram_code → contains only the diagram structure code (Do not include with Diagram() sentence). Do not include any comments, only python code
    - ai_response → the user-facing natural language response.  

    Important constraints:  
    - The ai_response **must never reveal, show, or mention any code, imports, or implementation details**.  
    - Do not explain how the code works or how to run it.  
    - The ai_response should sound natural, e.g., “Here’s the updated diagram based on your input.”  
    - All code must only appear inside `import_code` and `diagram_code`.
    - Do not generate this kind of sentence : "with Diagram()" in diagram_code

    Examples:

    import_code_example = \"\"\"  
    from diagrams import Diagram  
    from diagrams.aws.compute import EC2  
    from diagrams.aws.database import RDS  
    from diagrams.aws.network import ELB  
    \"\"\"

    diagram_code_example = \"\"\"  
    ELB("lb") >> [EC2("worker1"),  
    EC2("worker2"),  
    EC2("worker3"),  
    EC2("worker4"),  
    EC2("worker5")] >> RDS("events")  
    \"\"\"

    ai_response_example = "Here’s the diagram based on your input."

    Conversation:
    """

    response = model.with_structured_output(DiagramData).invoke([SystemMessage(content=MODEL_SYSTEM_MESSAGE)]+state["messages"])
    import_code = response.import_code
    diagram_code = response.diagram_code
    ai_response = response.ai_response
    return {"messages": [AIMessage(content=ai_response)],
            "import_code": import_code,
            "diagram_code": diagram_code
            }

def is_generated_diagram_code(state: State):
    if state["import_code"] and state["diagram_code"]:
        return True
    else:
        return False

def check_generated_code(state: State):
    is_valid, error_messages = check_modules(state["import_code"])
    return {"error_messages": error_messages}

def validate(state: State):
    if len(state["error_messages"]) > 0:
        return False
    else:
        return True

def get_documentation(state: State):
    print("Getting documentation...")
    error_messages = state["error_messages"]
    results = []
    for error in error_messages:
        results.append(qdrant_handler.query(error))
    return {"messages": [AIMessage(content=f"I encountered the following errors:\n{error_messages}\nHere are some relevant documentation snippets that might help:\n{results}")]}

def generate_diagram(state: State):
    print("Generating diagram...")
    python_diagram_code, error_message = generate(import_code=state["import_code"], 
                                   diagram_code=state["diagram_code"])
    return {
            "python_diagram_code": python_diagram_code, 
            "image_path": "diagram_image.png",
            "python_diagram_code_error": error_message}

model = ChatOpenAI(model=MODEL, api_key=API_KEY, temperature=1)
embedding = OpenAIEmbeddings(api_key=API_KEY, model=EMBEDDING_MODEL)
qdrant_handler = QdrantHandler(embedding=embedding)

# Build the graph directly
builder = StateGraph(State)
builder.add_node("assistant", assistant)
builder.add_node("check_generated_code", check_generated_code)
builder.add_node("get_documentation", get_documentation)
builder.add_node("generate_diagram", generate_diagram)

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
            "assistant", 
            is_generated_diagram_code, # the function that determines which node to go to next
            {True: "check_generated_code", False: END} # if the function returns True, go to action, otherwise end the graph
        )
builder.add_conditional_edges(
            "check_generated_code", 
            validate, # the function that determines which node to go to next
            {True: "generate_diagram", False: "get_documentation"} # if the function returns True, go to action, otherwise end the graph
        )
builder.add_edge("get_documentation", "assistant")
builder.add_edge("generate_diagram", END)

memory = MemorySaver()
agent = builder.compile(checkpointer=memory)  # <-- This is now a Graph

graph_image = agent.get_graph().draw_mermaid_png()
with open("agent2.png", "wb") as f:
    f.write(graph_image)

def invoke(message, thread_id="1"):
    config = {"configurable": {"thread_id": thread_id}}
    messages = [HumanMessage(content=message)]
    response = agent.invoke({"messages": messages}, config=config)
    image_path = response.get("image_path", None)
    python_diagram_code = response.get("python_diagram_code", None)
    return response["messages"][-1].content, image_path, python_diagram_code

if __name__ == "__main__":
    pass
    while True:
        user_message = input("You: ")
        if user_message.lower() == "exit":
            break
        response, image_path, python_diagram_code = invoke(user_message)
        print("Assistant:", response)
        print("Diagram image path:", image_path)
        print("Python diagram code:", python_diagram_code)


