from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.state import CompiledStateGraph


def my_create_agent(model: BaseChatModel, tools: list[BaseTool]) -> CompiledStateGraph:
    
    if tools:
        model = model.bind_tools(tools)

    def node(state: MessagesState) -> MessagesState:
        return {"messages": model.invoke(state["messages"])}
    
    builder = StateGraph(MessagesState)

    builder.add_node("node", node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "node")
    builder.add_conditional_edges("node", tools_condition, [END, "tools"])
    builder.add_edge("tools", "node")

    return builder.compile()