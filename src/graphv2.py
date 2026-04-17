from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal, Annotated
from operator import add
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.memory import InMemorySaver
from typing import get_origin, get_args, Union
from types import NoneType

import uuid

from state import ExtractionState, UserProfile

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

# class UserProfile(BaseModel):
#     name: Optional[str] = Field(default=None, description="User's full name")
#     company: Optional[str] = Field(default=None, description="Company the user works at")
#     role: Optional[str] = Field(default=None, description="User's job title or role")
#     location: Optional[str] = Field(default=None, description="Where the user is based")
#     interests: list[str] = Field(default_factory=list, description="Important interests or topics the user cares about")

def format_string_from_user_profile(user : UserProfile) -> str:
    return "\n".join([f"{k} : {v}" for k, v in user.model_dump().items()])

# class UserProfileList(BaseModel):
#     items: list[UserProfile] = Field(default_factory=list)

# class PlannerOutput(BaseModel):
#     target_ids_to_update: list[str]
#     reasoning_summary: str
#     new_person_count: int

# class ExtractionState(BaseModel):
#   messages: Annotated[list[BaseMessage], add]
#   existing: dict[str, UserProfile] = Field(default_factory=dict)
#   candidate: dict[str, UserProfile] = Field(default_factory=dict)
#   errors: dict[str, list[str]] = Field(default_factory=dict)
#   attempts: int = 0
#   patches: list[PatchProposal] = Field(default_factory=list)
#   plan: PlannerOutput | None = None


def route(state: ExtractionState)-> Literal["extract", "extract_updates"]:
  """deciding when to go to extract or extract_updates"""
  # checks whether there is `existing`,
  # if not returns "extract" if yes returns "extract_updates"
  existing = state.existing
  if existing:
    return "extract_updates"
  else:
    return "extract"

def planner_node(state: ExtractionState) -> ExtractionState:
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


def extract(state: ExtractionState) -> ExtractionState:
  """calls a llm_bound with tools (tools would be the desired structured schema) to get fully parsed candidate objects"""
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
  messages = state.messages
  llm_with_structure = llm.with_structured_output(UserProfile)
  result = llm_with_structure.invoke([SystemMessage(system_prompt)] + messages)
  return {"candidate" : {str(uuid.uuid4()): result}}


  # the problem: Define a separate patch schema, PatchProposal. In TrustCall called PatchDoc

def extract_updates(state: ExtractionState) -> ExtractionState:
  """calls a llm_bound with tools (tools should use a patch-producing schema, not the full
target schema directly. ) but takes `existing` into account to return only what's
changed into ExtractionState"""
  # passes both `existing` and `state.messages` and calls a tool calling model that adapts to a patch schema
  # The patch schema needs at least two things: a target identifier and a list of patch operations.
  # updates state.patches
  messages = state.messages
  existing = state.existing

  # formatted_class = "\n".join([f"{k}: {v.description}, type of this field: {annotation_to_text(v.annotation)}"
  #                                     for k, v in UserProfile.model_fields.items()])
  
  format_class = format_string_from_schema(UserProfile)

  format_existing = "\n".join([f"Obj_id = {k}:\n{format_string_from_user_profile(v)}\n"
                                                      + "-" * 60
                                                      + "\n"
                                                      for k, v in existing.items()])

  system_prompt_updates = """
You are updating existing structured user profile objects.

Your job is not to rewrite full objects. Your job is to return only the changes needed, as patch operations.

The patch operations must be consistent with the target UserProfile schema below. Any path you modify must correspond to a valid field in that schema, and any value you provide must match the field's meaning and type.

UserProfile schema:
{formatted_class}

Existing objects:
{formatted_existing}

Rules:
- Use the existing objects as the baseline truth.
- Use only information explicitly stated or strongly implied in the conversation.
- Do not guess or invent facts.
- Do not include fields that do not need to change.
- Return patch operations only for fields that should be added, removed, or replaced.
- Each patch proposal must set target_id to exactly one of the object IDs shown in Existing objects.
- Do not invent new target_id values.
- Every patch path must correspond to a valid field in the UserProfile schema.
- Every patch value must be compatible with the field type described in the UserProfile schema.
- If a field is optional and the conversation does not support changing it, do not create a patch for it.
- If no change is needed for an object, do not create a patch for it.
- The output must match the patch schema exactly.
"""

  system_msg = SystemMessage(system_prompt_updates.format(formatted_class=format_class,
                                                          formatted_existing=format_existing))

  llm_with_structure = llm.with_structured_output(PatchProposalList)
  result = llm_with_structure.invoke([system_msg] + messages)
  return {"patches" : result.items}


def apply_patch(state: ExtractionState) -> ExtractionState:
  """deterministic step to apply state.patches to state.existing and writes result into state.candidate"""
  # passes state.patches and applies it to state.existing
  # returns the applied existing to state.candidate
  print(state.patches)

def validate(state: ExtractionState) -> ExtractionState:
  """validates the resulting structure with pydantic. If errors catches ValidationError and returns list of strings"""
  # passes the structure in state.candidate
  # returns either a List[str] of errors into state.errors[target_id] or None

def validate_route(state: ExtractionState)-> Literal["patch", "__end__"]:
  """deciding when to go to patch or to finish the graph"""
  # checks whether there are state.errors,
  # if not goes to END if yes returns "patch"
  errors = state.errors
  if errors:
    return "patch"
  else:
    return END

def patch(state: ExtractionState) -> ExtractionState:
  """retries fixing the structure if validate found a `ValidationError`"""
  # passes the structure with errors and the `ValidationError` in state.errors
  # returns a fixed structure to state.candidate


# memory = InMemorySaver()

builder = StateGraph(ExtractionState)

# builder.add_node("extract", extract)
# builder.add_node("extract_updates", extract_updates)
# builder.add_node("apply_patch", apply_patch)

# builder.add_conditional_edges(START, route, ["extract", "extract_updates"])
# builder.add_edge("extract_updates", "apply_patch")
# builder.add_edge("apply_patch", END)

builder.add_node("planner", planner_node)
builder.add_edge(START, "planner")
builder.add_edge("planner", END)

graph = builder.compile()
# graph = builder.compile(checkpointer=memory)
