from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field
from typing import Annotated

from src.utilities import save_graph
from src.tools import add, multiply, divide, subtract
from src.builder import my_create_agent

load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [add, multiply, divide, subtract]

class Subagent(BaseModel):
    "Configuration for specialized subagent"
    name: Annotated[str, Field(description="This is the name of the subagent. Also know as `agent type`")]
    description: Annotated[str, Field(description="This is reason why the agent should be called so main agent can select")]
    prompt: Annotated[str, Field(description="This is the system prompt passed to the subagent when creating it")]
    tools: Annotated[list[str], Field(description="Tools available to this subagent")] = Field(default_factory=list)

graph = my_create_agent(model=llm, tools=tools)

save_graph(graph, "mermaid.png")
