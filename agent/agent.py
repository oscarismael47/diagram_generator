import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import MessagesState
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.graph import CurveStyle
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

class DiagramData(BaseModel):
    """
    Data model for storing diagram generation information.

    Attributes:
        import_code (str): The import statements required for the diagram.
        body_code (str): The code that defines the diagram structure.
        ai_response (str): The AI-generated response or explanation.
    """
    import_code: str = Field(..., description="The import statements required for the diagram.")
    body_code: str = Field(..., description="The code that defines the diagram structure.")
    ai_response: str = Field(..., description="The AI-generated response or explanation.")

class State(MessagesState):
    import_code: str
    body_code: str
    python_body_code: str
    image_path: str
    error_messages: list[str]

def assistant(state: State):
    MODEL_SYSTEM_MESSAGE = """
    You are a helpful assistant that generates Cloud Architecture Diagrams (AWS, GCP, Azure) based on user input.

    Your responsibilities:
    1. Answer user questions in a clear, concise, and friendly way.  
    2. Ask clarifying questions when requirements or preferences are ambiguous.  
    3. Generate the correct `import_code` and `body_code` (Python code using the diagrams library) strictly according to the user’s input.  
    4. Revise and improve diagrams when the user provides feedback.  
    5. After successful diagram generation, confirm completion and provide a description of the architecture shown in the diagram.

    Output format:
    Always return exactly three fields:
    - `import_code` → contains only the necessary Python imports. **No comments.**  
    - `body_code` → contains only the diagram structure code. **No comments.**  
    - `ai_response` → a natural-language response for the user. **Never reveal or describe code, imports, or implementation details.**

    Important constraints:
    - Only generate `import_code` and `body_code` when the user explicitly requests diagram/image generation or an update.  
    - The `ai_response` must be natural, e.g., “Here’s the updated diagram based on your input.”  
    - Never explain how the code works or how to run it.  
    - All code must only appear inside `import_code` and `body_code`.  
    - `import_code` must always begin with:  
    `from diagrams import Diagram`  
    - `body_code` must always begin with:  
    `with Diagram("Diagram name", show=False, filename=filename_value, outformat="png", graph_attr=graph_attr_value):`  
        - Use the existing variable `filename_value` (do not redefine it).  
        - Use the existing variable `graph_attr_value` (do not redefine it).  
    - If the user requests an **adjustment or update**, you may reuse and build upon the last provided `import_code` and `body_code` instead of starting from scratch.  

    Context:
    This is the last working `import_code` (may be empty):  
    {import_code}  

    This is the last working `body_code` (may be empty):  
    {body_code}  

    Examples of good responses:

    Example 1:
    import_code_example = \"\"\"  
    from diagrams import Diagram  
    from diagrams.aws.compute import EC2  
    from diagrams.aws.database import RDS  
    from diagrams.aws.network import ELB  
    \"\"\"

    body_code_example = \"\"\"  
    with Diagram("Diagram", show=False, filename=filename_value, outformat="png", graph_attr=graph_attr_value):  
        ELB("lb") >> [EC2("worker1"),  
                    EC2("worker2"),  
                    EC2("worker3"),  
                    EC2("worker4"),  
                    EC2("worker5")] >> RDS("events")  
    \"\"\"

    ai_response_example = "The diagram has been generated successfully. This AWS architecture uses an ELB to distribute traffic across five EC2 instances, which connect to a central RDS database, providing scalability, high availability, and managed data storage."
    """
    
    import_code = state.get("import_code", "")
    body_code = state.get("body_code", "")

    system_msg = MODEL_SYSTEM_MESSAGE.format(import_code=import_code, body_code=body_code)

    response = model.with_structured_output(DiagramData).invoke([SystemMessage(content=system_msg)]+state["messages"])
    import_code = response.import_code
    body_code = response.body_code
    ai_response = response.ai_response
    return {"messages": [AIMessage(content=ai_response)],
            "import_code": import_code,
            "body_code": body_code
            }

def has_body_code_generated(state: State):
    print("Checking if diagram code is generated...")
    if state["import_code"] and state["body_code"]:
        return True
    else:
        return False

def create_diagram_image(state: State):
    print("Generating diagram...")
    python_body_code, error_message, image_path = generate(import_code=state["import_code"], 
                                   body_code=state["body_code"])
    if error_message:
        ai_message = AIMessage(content=f"Error generating diagram: **{error_message}** \n. This code generated the error:\n{python_body_code}. Please fix the code.", 
                               response_metadata = {
                                   "step": "create_diagram_image",
                                   "error_messages": [error_message],
                                   "python_body_code": python_body_code,               
                               })

        return {"messages": [ai_message],
                "python_body_code": python_body_code,
                "image_path": image_path
            }
    else:
        return {
            "python_body_code": python_body_code,
            "image_path": image_path
        }

def validate_imported_modules(state: State):
    print("Validating imported modules...")
    _, error_messages = check_modules(state["import_code"])
    return {"error_messages": error_messages}


def is_diagram_image_created(state: State):
    print("Checking if diagram image is created...")
    if state["python_body_code"] and state["image_path"] is not None:
        return True
    else:
        return False

def has_no_import_errors(state: State):
    print("Checking for import errors...")
    if len(state["error_messages"]) > 0:
        return False
    else:
        return True

def fetch_documentation_for_errors(state: State):
    print("Fetching documentation for errors...")
    error_messages = state["error_messages"]
    print("Error messages:", error_messages)
    results = []
    for error in error_messages:
        results.append(qdrant_handler.query(error))
    ai_message = AIMessage(content=f"Errors of importation encountered:\n{error_messages}\nHere are some relevant documentation snippets that might help:\n{results}",
                           response_metadata = {
                                    "step": "fetch_documentation_for_errors",
                                    "error_messages": error_messages,
                                    "documentation": results
                               })
    return {"messages": [ai_message]}

model = ChatOpenAI(model=MODEL, api_key=API_KEY, temperature=1)
embedding = OpenAIEmbeddings(api_key=API_KEY, model=EMBEDDING_MODEL)
qdrant_handler = QdrantHandler(embedding=embedding)

# Build the graph directly
builder = StateGraph(State)
builder.add_node("assistant", assistant)
builder.add_node("validate_imported_modules", validate_imported_modules)
builder.add_node("fetch_documentation_for_errors", fetch_documentation_for_errors)
builder.add_node("create_diagram_image", create_diagram_image)

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
            "assistant", 
            has_body_code_generated, # the function that determines which node to go to next
            {True: "validate_imported_modules", False: END} # if the function returns True, go to action, otherwise end the graph
        )
builder.add_conditional_edges(
            "validate_imported_modules", 
            has_no_import_errors, # the function that determines which node to go to next
            {True: "create_diagram_image", False: "fetch_documentation_for_errors"} # if the function returns True, go to action, otherwise end the graph
        )
builder.add_edge("fetch_documentation_for_errors", "assistant")
builder.add_conditional_edges(
            "create_diagram_image", 
            is_diagram_image_created, # the function that determines which node to go to next
            {True: END, False: "assistant"} # if the function returns True, go to action, otherwise end the graph
        )

memory = MemorySaver()
agent = builder.compile(checkpointer=memory)  # <-- This is now a Graph

# graph_image = agent.get_graph(xray=True).draw_mermaid_png(curve_style=CurveStyle.LINEAR)
# with open("agent.png", "wb") as f:
#    f.write(graph_image)

def invoke(message, thread_id="1"):
    config = {"configurable": {"thread_id": thread_id}}
    messages = [HumanMessage(content=message)]
    response = agent.invoke({"messages": messages}, config=config)
    image_path = response.get("image_path", None)
    python_body_code = response.get("python_body_code", None)
    messages = response.get("messages", [])
    return response["messages"][-1].content, image_path, python_body_code, messages

if __name__ == "__main__":
    pass
    while True:
        user_message = input("You: ")
        if user_message.lower() == "exit":
            break
        response, image_path, python_body_code, messages = invoke(user_message)
        print("Assistant:", response)
        print("Diagram image path:", image_path)
        print("Python diagram code:", python_body_code)
        print("Messages:", messages)
        print("-----")