from dotenv import load_dotenv
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field
from typing import Annotated

from src.utilities import save_graph
from src.tools import add, multiply, divide, subtract, web_search
from src.my_create_agent import my_create_agent

load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)

class Subagent(BaseModel):
    "Configuration for specialized subagent"
    name: Annotated[str, Field(description="This is the name of the subagent. Also know as `agent type`")]
    description: Annotated[str, Field(description="This is reason why the agent should be called so main agent can select")]
    prompt: Annotated[str, Field(description="This is the system prompt passed to the subagent when creating it")]
    tools: Annotated[list[BaseTool], Field(description="Tools available to this subagent")] = Field(default_factory=list)


SIMPLE_MATH_INSTRUCTIONS = "You're a calculator. Choose the operation or operations needed to make the calculatations. Make one or more Tool Calls in parallel to get the information needed. Keep on making Tool Calls until you have the final answer."

math_sub_agent = Subagent(name="math_agent",
                          description="This agent should be used when a math operation needs to be used",
                          prompt=SIMPLE_MATH_INSTRUCTIONS,
                          tools=[add, multiply, divide, subtract])


SIMPLE_RESEARCH_INSTRUCTIONS = """You are a researcher. Research the topic provided to you. IMPORTANT: Just make a single call to the web_search tool and use the result provided by the tool to answer the provided topic."""

search_sub_agent = Subagent(name="search_agent",
                            description= "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
                            prompt= SIMPLE_RESEARCH_INSTRUCTIONS,
                            tools= [web_search])


subagents = [math_sub_agent, search_sub_agent]

agents = {agent.name: my_create_agent(model=llm, tools=agent.tools, prompt=agent.prompt) for agent in subagents}

other_agents_string = "\n".join([f"{agent.name} : {agent.description}" for agent in subagents])


TASK_DESCRIPTION_PREFIX = """Delegate a task to a specialized sub-agent with isolated context. Available agents for delegation are:
{other_agents}
"""

TASK_DESCRIPTION = TASK_DESCRIPTION_PREFIX.format(other_agents_string)

"""
I need to create the tool I will pass to the main agent so it will call the correct subagent.
This tool, called task, is going to:
1. Receive as params: 
    agents: list of subagents it can call. This subagents are going to be compiled already
    description as a `@tool` param: the description of how it has to chose over the subagents it has which includes all the descriptions of each agent.

"""


graph = my_create_agent(model=llm, tools=tools) 



# 1. Create the main

save_graph(graph, "mermaid.png")
