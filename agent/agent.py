import os
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import MessagesState
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI model with the API key and model name from Streamlit secrets
MODEL = os.getenv("OPENAI_MODEL")
API_KEY = os.getenv("OPENAI_KEY")

class State(MessagesState):
    pass

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

llm = ChatOpenAI(model=MODEL, api_key=API_KEY, temperature=0.7)
# Initialize Tavily Search Tool
tavily_search_tool = TavilySearch(max_results=2)
tools = [tavily_search_tool]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=tools)



# Build the graph directly
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", tool_node)

builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

builder.add_edge("tools", "chatbot")
builder.add_edge(START, "chatbot")
agent = builder.compile()  # <-- This is now a Graph

# Optionally, generate the image (not required for the export)
graph_image = agent.get_graph().draw_mermaid_png()
with open("static/chatbot_agent.png", "wb") as f:
    f.write(graph_image)