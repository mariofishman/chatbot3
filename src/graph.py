from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessagesState, StateGraph, START, END

from pydantic import BaseModel, Field
from typing import Annotated

from src.utilities import save_graph
from src.tools import add, multiply, divide, subtract

load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)

class Subagent(BaseModel):
    "Configuration for specialized subagent"
    name: Annotated[str, Field(description="This is the name of the subagent. Also know as `agent type`")]
    description: Annotated[str, Field(description="This is reason why the agent should be called so main agent can select")]
    prompt: Annotated[str, Field(description="This is the system prompt passed to the subagent when creating it")]
    tools: Annotated[list[str], Field(description="Tools available to this subagent")] = Field(default_factory=list)



tools = [add, multiply, divide, subtract]
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
