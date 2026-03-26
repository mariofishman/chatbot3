from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
# from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessagesState, StateGraph, START, END

from src.utilities import save_graph

load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)

@tool
def add(a: float, b: float) -> float:
    """
    This function should be used to add two numbers
    """
    return a + b

@tool
def multiply(a: float, b: float) -> float:
    """
    This function should be used to multiply two numbers
    """
    return a * b

@tool
def divide(a: float, b: float) -> float:
    """
    This function should be used to divide two numbers
    """
    return a / b

tools = [add, multiply, divide]
llm_with_tools = llm.bind_tools(tools)

def node(state: MessagesState) -> MessagesState:
    return {"messages": llm_with_tools.invoke(state["messages"])}

builder = StateGraph(MessagesState)

builder.add_node("node", node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "node")
builder.add_conditional_edges("node", tools_condition, [END, "tools"])
builder.add_edge("tools", "node")

graph = builder.compile()
save_graph(graph, "mermaid.png")
