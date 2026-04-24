from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import Literal, get_origin, get_args, Union
from types import NoneType

import uuid

from state import MainState, ExtractAgentState, UpdateAgentState, UserProfile, UserProfileList, MessageSelectionOutput

load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def annotation_to_text(annotation) -> str:
    """Convert a Python/Pydantic field annotation into a short human-readable string.

This helper is used to format schema fields for prompts. It currently handles
the annotation patterns used in the notebook prototype:

- plain types, such as str
- optional fields, such as Optional[str]
- list fields, such as list[str]

Examples:
- str -> "str"
- Optional[str] -> "Optional[str]"
- list[str] -> "list[str]"
"""

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is None:
        return getattr(annotation, "__name__", str(annotation))

    if origin is Union and NoneType in args:
        non_none_args = [arg for arg in args if arg is not NoneType]
        if len(non_none_args) == 1:
            return f"Optional[{annotation_to_text(non_none_args[0])}]"

    if origin is list:
        return f"list[{annotation_to_text(args[0])}]"

    return str(annotation)

def format_string_from_schema(cls) -> str:
    return "\n".join([f"{k}: {v.description}, type of this field: {annotation_to_text(v.annotation)}"
        for k, v in cls.model_fields.items()])

def format_messages(messages: list[BaseMessage])-> str:
    return "\n".join([f"{m.type}: {m.content}; id: {m.id}" for m in messages if m.type == "ai" or m.type == "human"]) 

def format_string_from_user_profile(user : UserProfile) -> str:
    return "\n".join([f"{k} : {v}" for k, v in user.model_dump().items()])

def planner_node(state: MainState) -> MainState:
    llm_with_structure = llm.with_structured_output(MessageSelectionOutput)

    existing_profiles = state.existing 

    formatted_existing = "\n".join(
        [
            f"Obj_id = {k}:\n{format_string_from_user_profile(v)}\n"
            + "-" * 60
            + "\n"
            for k, v in existing_profiles.items()
        ]
    )

    formatted_messages = format_messages(state.messages)

    PLANNER_PROMPT = """
You are a planner for a structured memory extraction system.

Your job is only to identify which human messages are relevant for:
1. creating or extracting new user profiles
2. updating existing user profiles

Existing profiles:
{formatted_existing}

Existing messages:
{formatted_messages}

Rules:
- Only return IDs that belong to human messages.
- Use the IDs exactly as provided.
- Ignore the system message.
- Include every human message that contains profile-relevant information.
- A single human message may be relevant for both creating new profiles and updating existing profiles.
- If a message contains update information, add an item to relevant_for_update_links with the message_id and the correct user_profile_ids.
- If a message contains create information, add an item to relevant_for_create_links with the message_id and the number of new people mentioned in that message.
- The same message ID may appear in relevant_for_create_links and also inside relevant_for_update_links.
- Do not invent IDs.
- Do not invent existing user profile IDs.

Return output that matches the MessageSelectionOutput schema exactly.
"""

    
    system_msg = SystemMessage(PLANNER_PROMPT.format(formatted_existing=formatted_existing, formatted_messages=formatted_messages))

    result = llm_with_structure.invoke([system_msg, *state.messages])

    return {"plan": result}


def extract_node(state: ExtractAgentState) -> ExtractAgentState:
    """calls a llm with structured output to get fully parsed candidate objects"""
    # passes state.messages and process these with a tool calling model to get structured output according to a Schema
    # updates candidate in the state
    
    # unpack the message ids from CreateLink object into a list of message ids
    relevant_message_ids = [link.message_id for link in state.plan.relevant_for_create_links]

    # DEBUGGING
    print(f"DEBUGGING: relevant msg ids: {relevant_message_ids}")
    
    # DEBUGGING
    print(f"DEBUGGING: message ids: {[msg.id for msg in state.messages]}")

    relevant_messages = format_messages([msg for msg in state.messages if msg.id in relevant_message_ids])
    
    # DEBUGGING
    print(f"DEBUGGING: formatted msgs: {relevant_messages}")

    system_prompt = f"""
Extract structured user profile information from the conversation.

Rules:
- Use only information explicitly stated or strongly implied in the messages.
- Do not guess or invent facts.
- If a field is unknown, leave it null.
- For list fields, include only items clearly supported by the conversation.
- Return output that matches the target schema exactly.

PLANNER INSTRUCTION:
{state.plan.reasoning_summary_for_create}

TAKE INTO ACCOUNT THESE MESSAGE(S):
{relevant_messages}
"""
    # FOR DEBUGGING
    print(f"DEBUGGING: prompt is: \n{system_prompt}")

    structured_llm = llm.with_structured_output(UserProfileList)
    result = structured_llm.invoke([SystemMessage(system_prompt)])

    # FOR DEBUGGING
    print(f"DEBUGGING: structured output: {result}")

    new = {str(uuid.uuid4()): usr for usr in result.items}
    return {"existing": new} 

def route(state: MainState) -> Literal["extract", "__end__"]:
    plan = state.plan
    if plan.relevant_for_create_links:
        return "extract"
    return "__end__"

builder = StateGraph(MainState)

builder.add_node("planner", planner_node)
builder.add_node("extract", extract_node)

builder.add_conditional_edges("planner", route)
builder.add_edge(START, "planner")
builder.add_edge("extract", END)


config = {"configurable": {"thread_id": "1"}}
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)
