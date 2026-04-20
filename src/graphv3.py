from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.memory import InMemorySaver
from typing import get_origin, get_args, Union
from types import NoneType

import uuid

from state import MainState, ExtractAgentState, UpdateAgentState, UserProfile, PlannerOutput, UserProfileList

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
    return "\n".join([f"{m.type}: {m.content}" for m in messages if m.type == "ai" or m.type == "human"]) 

def format_string_from_user_profile(user : UserProfile) -> str:
    return "\n".join([f"{k} : {v}" for k, v in user.model_dump().items()])


def planner_node(state: MainState) -> MainState:
    llm_with_structure = llm.with_structured_output(PlannerOutput)

    existing_profiles = state.existing 

    format_existing = "\n".join([f"Obj_id = {k}:\n{format_string_from_user_profile(v)}\n"
                                                    + "-" * 60
                                                    + "\n"
                                                    for k, v in existing_profiles.items()])

    PLANNER_PROMPT = """
You are a planner for a structured memory extraction system.

Your job is only to decide:
1. which existing profile ids should be updated
2. how many new profile objects should be created

You are not extracting profile fields.
You are not producing patch operations.
You are not validating data.
You are only planning the next actions.

Inputs you will receive:
- the conversation messages:
{formatted_messages}

- the currently existing profile objects, each with its object id:
{formatted_existing}

Return output that matches the PlannerOutput schema exactly.

Rules:
- If the message clearly adds, corrects, removes, or refines information about an existing profile, include that profile id in target_ids_to_update.
- Treat any newly stated profile fact as a possible update, including name details, company, role, location, interests, preferences, and important personal or professional attributes.
- If a message adds a new interest, topic of interest, or preference for an existing person, that counts as an update and the person's id must be included in target_ids_to_update.
- A profile should be selected for update even if only one field changes.
- If the message clearly introduces a different person who is not one of the existing profiles, increase new_person_count accordingly.
- A single message may both update existing profiles and introduce new people.
- Do not map a newly mentioned person onto an existing profile unless the message provides clear evidence they are the same person.
- If the message gives a different name from every existing profile and does not provide alias or identity-linking evidence, treat that person as new.
- Shared facts such as company, role, or location are not enough by themselves to conclude that a new named person is actually an existing profile.
- When in doubt between "update existing" and "create new", prefer creating a new person rather than overwriting an unrelated existing profile.
- Use only information explicitly stated or strongly implied in the conversation.
- Do not guess.
- Do not invent object ids.
- Only use target ids that are present in the provided existing objects.
- If no existing object should be updated, return an empty list for target_ids_to_update.
- If no new person should be created, return 0 for new_person_count.
- Keep reasoning_summary short, factual, and high level.
"""
    
    system_msg = SystemMessage(PLANNER_PROMPT.format(formatted_messages=format_messages(state.messages),
                                                     formatted_existing=format_existing))

    result = llm_with_structure.invoke([system_msg])

    return {"plan": result}

# class PlannerOutput(BaseModel):
#     target_ids_to_update: list[str]
#     reasoning_summary: str
#     new_person_count: int

def extract_node(state: ExtractAgentState) -> ExtractAgentState:
    """calls a llm with structured output to get fully parsed candidate objects"""
    # passes state.messages and process these with a tool calling model to get structured output according to a Schema
    # updates candidate in the state
    system_prompt = """
Extract structured user profile information from the conversation.

Rules:
- Use only information explicitly stated or strongly implied in the messages.
- Do not guess or invent facts.
- If a field is unknown, leave it null.
- For list fields, include only items clearly supported by the conversation.
- Return output that matches the target schema exactly.
"""
    structured_llm = llm.with_structured_output(UserProfileList)
    result = structured_llm.invoke([SystemMessage(system_prompt)] + state.messages)
    return result 


builder = StateGraph(MainState)

builder.add_node("planner", planner_node)
builder.add_edge(START, "planner")
builder.add_edge("planner", END)

graph = builder.compile()
