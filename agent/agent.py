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
    You are a helpful assistant that generates Cloud (AWS, GCP, Azure) Architecture Diagrams based on user input.

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
    - Generate import_code and diagram_code only if the user requests diagram or image generation or updating
    - The ai_response **must never reveal, show, or mention any code, imports, or implementation details**.  
    - Do not explain how the code works or how to run it.  
    - The ai_response should sound natural, e.g., “Here’s the updated diagram based on your input.”  
    - All code must only appear inside `import_code` and `diagram_code`.
    - It is important to add 'from diagrams import Diagram' at the beginning of the import_code.
    - Do not generate this kind of sentence : "with Diagram()" in diagram_code

    This is the last import_code that generated the correct diagram (it may be empty).
    {import_code}
    This is the last diagram_code that generated the correct diagram (it may be empty).
    {diagram_code}

    Here are some examples of good responses:
    Example 1:

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


    import_code = state.get("import_code", "")
    diagram_code = state.get("diagram_code", "")

    system_msg = MODEL_SYSTEM_MESSAGE.format(import_code=import_code, diagram_code=diagram_code)

    response = model.with_structured_output(DiagramData).invoke([SystemMessage(content=system_msg)]+state["messages"])
    import_code = response.import_code
    diagram_code = response.diagram_code
    ai_response = response.ai_response
    return {"messages": [AIMessage(content=ai_response)],
            "import_code": import_code,
            "diagram_code": diagram_code
            }

def has_diagram_code_generated(state: State):
    print("Checking if diagram code is generated...")
    if state["import_code"] and state["diagram_code"]:
        return True
    else:
        return False

def create_diagram_image(state: State):
    print("Generating diagram...")
    python_diagram_code, error_message, image_path = generate(import_code=state["import_code"], 
                                   diagram_code=state["diagram_code"])
    if error_message:
        ai_message = AIMessage(content=f"Error generating diagram: {error_message} \n. This code generated the error: {python_diagram_code}")
        return {"messages": [ai_message],
                "python_diagram_code": python_diagram_code,
                "image_path": image_path
            }
    else:
        return {
            "python_diagram_code": python_diagram_code,
            "image_path": image_path
        }

def validate_imported_modules(state: State):
    print("Validating imported modules...")
    _, error_messages = check_modules(state["import_code"])
    return {"error_messages": error_messages}


def is_diagram_image_created(state: State):
    print("Checking if diagram image is created...")
    if state["python_diagram_code"] and state["image_path"] is not None:
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
    results = []
    for error in error_messages:
        results.append(qdrant_handler.query(error))
    return {"messages": [AIMessage(content=f"I encountered the following errors:\n{error_messages}\nHere are some relevant documentation snippets that might help:\n{results}")]}

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
            has_diagram_code_generated, # the function that determines which node to go to next
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