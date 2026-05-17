from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, Send, interrupt
from pydantic import ValidationError
from typing import Literal, Sequence, get_origin, get_args, Union
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

# ----------------------------
# 1. Parent state
# ----------------------------
"""
MainState
class MainState(BaseModel):
    messages: Annotated[list[BaseMessage], add]
    existing: Annotated[dict[str, UserProfile], merge_profiles] = Field(default_factory=dict)
    plan: MessageSelectionOutput | None = None
"""

# ----------------------------
# 2. Extract Sub Agent State and nodes
# ----------------------------

"""
class ExtractAgentState(MainState):
    has_create_mismatch: bool = False
    human_prompt: str | None = None
"""

def extract_node(state: ExtractAgentState) -> Command[Literal["human", "__end__"]]:
    """calls a llm with structured output to get fully parsed candidate objects"""
    # passes state.messages and process these with a tool calling model to get structured output according to a Schema
    # updates candidate in the state
    
    formatted_messages = format_messages(state.messages)

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
{formatted_messages}
"""
    
    # FOR DEBUGGING
    # print(f"DEBUGGING: prompt is: \n{system_prompt}")

    structured_llm = llm.with_structured_output(UserProfileList)
    result = structured_llm.invoke([SystemMessage(system_prompt)])

    # FOR DEBUGGING
    # result = UserProfileList(items=[UserProfile(name="Fake Test Person")])

    # FOR DEBUGGING
    # print(f"DEBUGGING: structured output: {result}")

    total_new_person_count = sum([link.new_person_count for link in state.plan.relevant_for_create_links])
    # print(f"DEBUGGING: new UserProfile count: {total_new_person_count}")

    if total_new_person_count != len(result.items):
        retry_prompt = f"""
Your previous extraction was incorrect.

The planner expected {total_new_person_count} new people, but you returned {len(result.items)} profiles.

The planner's summary of the create-side meaning is:
{state.plan.reasoning_summary_for_create}

Re-read the same create-relevant messages and try again.

Return output that matches the UserProfileList schema exactly.
Return exactly {total_new_person_count} distinct new UserProfile objects.
Do not guess or invent facts.
If a field is unknown, leave it null.
For list fields, include only items clearly supported by the messages.

The create-relevant messages are:
{formatted_messages}
"""
        result = structured_llm.invoke([SystemMessage(retry_prompt)])

        # print(f"DEBUGGING: retry prompt is:\n{retry_prompt}")

    if total_new_person_count != len(result.items):
        names_text = "\n".join([person.name for person in result.items])
        human_prompt = f"""
- The planner thought you should create {total_new_person_count} but the model only created {len(result.items)}
- The planner also provided this reasoning for create {state.plan.reasoning_summary_for_create} and the model
extracted only {names_text}. Dear human, please, return in JSON format
the profiles that the model should have extracted. 
"""
        return Command(
            update={"has_create_mismatch" : True,
                    "human_prompt": human_prompt,
                    },
            goto="human"
        )
    else:
        new = {str(uuid.uuid4()): usr for usr in result.items}
        return Command(
            update= {"existing": new},
            goto = "__end__"
        )
    
def human(state: ExtractAgentState) -> ExtractAgentState:
    payload = interrupt(state.human_prompt)
    # Expect resume payload in UserProfileList JSON shape, e.g. {"items": [...]}
    while True:
        try:
            validated_result = UserProfileList.model_validate(payload)
            break
        except ValidationError as e:
            payload = interrupt(
                {
                    "message": "The payload did not match the expected UserProfileList JSON shape. Please try again.",
                    "errors": e.errors(),
                    "expected_format": {
                        "items": [
                            {
                                "name": "Lucia Romero",
                                "company": None,
                                "role": "Startup Lawyer",
                                "location": "Lima",
                                "interests": [],
                            }
                        ]
                    },
                }
            )
    new = {str(uuid.uuid4()): usr for usr in validated_result.items}
    return {"existing" : new}

extract_builder = StateGraph(ExtractAgentState)
extract_builder.add_node("extract", extract_node)
extract_builder.add_node("human", human)
extract_builder.add_edge(START, "extract")
extract_builder.add_edge("human", END)

extract_subgraph = extract_builder.compile()


# ----------------------------
# 3. Update Sub Agent State and nodes
# ----------------------------

"""
class UpdateAgentState(MainState):
    candidate: dict[str, UserProfile] = Field(default_factory=dict)
    errors: dict[str, list[str]] = Field(default_factory=dict)
    attempts: int = 0
    patches: list[PatchProposal] = Field(default_factory=list)
"""

def update_patches(state: UpdateAgentState) -> UpdateAgentState:
    """Generate patch proposals for the filtered update branch.

    This node is the update-side equivalent of the create extractor.
    It should read only the already-filtered update context prepared by the
    parent wrapper:

    - `state.messages`: only the update-relevant messages
    - `state.existing`: only the target profiles selected by the planner
    - `state.plan`: only the narrowed update-side planner information

    Its only job is to call the model and produce a `PatchProposalList`
    describing how each selected existing profile should be updated.

    It should not apply patches, validate results, or commit changes.
    """
    pass

def apply_patch(state: UpdateAgentState) -> UpdateAgentState:
    """Apply proposed patches into update-local candidate state.

    This node should deterministically apply the patch proposals created by
    `update_patches` to the filtered `state.existing` profiles and write the
    updated intermediate results into update-local working state.

    It should not ask the model for new patches, validate the patched
    profiles, or merge anything into top-level parent state.
    """
    pass

def route_patches(state: UpdateAgentState) -> Literal["patch", "commit"]:
    """Choose whether the update branch should repair or finish.

    This routing function should inspect update-local validation results and
    decide between:

    - `"patch"` when there are validation errors that still need repair
    - `"commit"` when the candidate profiles are valid and ready to return

    It should not modify state directly.
    """
    pass

def validate(state: UpdateAgentState) -> UpdateAgentState:
    """Validate patched candidates and record update-local errors.

    This node should inspect the candidate profiles produced by
    `apply_patch`, run deterministic validation checks, and store any errors
    in update-local state.

    It should not generate new patches or commit final results.
    """
    pass

def patch(state: UpdateAgentState) -> UpdateAgentState:
    """Repair invalid candidates using validation feedback.

    This node should use the validation errors recorded in update-local state
    to ask the model for a corrective patching step, or otherwise repair the
    invalid candidate profiles.

    Its output should prepare the branch for another deterministic validation
    pass.
    """
    pass

def commit(state: UpdateAgentState) -> UpdateAgentState:
    """Return committed update results from the update subgraph.

    This node should take the validated update-local candidates and return the
    final partial `existing` update that the parent graph can merge into
    top-level `MainState.existing` through the reducer.

    It should not return the full parent state, only the committed update
    slice for the selected target profiles.
    """
    pass


update_builder = StateGraph(UpdateAgentState)

update_builder.add_node("update_patches", update_patches)
update_builder.add_node("apply_patch", apply_patch)
update_builder.add_node("validate", validate)
update_builder.add_node("patch", patch)
update_builder.add_node("commit", commit)

update_builder.add_edge(START, "update_patches")
update_builder.add_edge("update_patches", "apply_patch")
update_builder.add_edge("apply_patch", "validate")
update_builder.add_conditional_edges("validate", route_patches)
update_builder.add_edge("patch", "validate")
update_builder.add_edge("commit", END)

update_subgraph = update_builder.compile()

# ----------------------------
# 4. Parent Nodes and Wrapper nodes
# ----------------------------


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

def run_extract_subgagent(state: MainState) -> MainState:
    # unpack the message ids from CreateLink object into a list of message ids
    relevant_message_ids = [link.message_id for link in state.plan.relevant_for_create_links]

    # DEBUGGING
    # print(f"DEBUGGING: relevant msg ids: {relevant_message_ids}")
    
    # DEBUGGING
    # print(f"DEBUGGING: message ids: {[msg.id for msg in state.messages]}")

    relevant_messages = [msg for msg in state.messages if msg.id in relevant_message_ids]
    
    # DEBUGGING
    # print(f"DEBUGGING: formatted msgs: {relevant_messages}")

    updated_plan = MessageSelectionOutput(
                                    reasoning_summary_for_update = "",
                                    relevant_for_update_links = [],
                                    reasoning_summary_for_create = state.plan.reasoning_summary_for_create,
                                    relevant_for_create_links = state.plan.relevant_for_create_links
                                    )

    sub_state = {"plan" : updated_plan,
                 "messages" : relevant_messages,
                 "existing" :{}}
    result = extract_subgraph.invoke(sub_state)
    return {
        "existing": result["existing"]
    }

def fan_out_updates(state: MainState) -> list[Send]:
    # I need to filter existing to only pass to "existing" the UserProfile with user_profile_ids shown in the list of UpdateLink.

    relevant_for_update_links_by_user_id = {}

    for link in state.plan.relevant_for_update_links:
        for user_id in link.user_profile_ids:
            relevant_for_update_links_by_user_id.setdefault(user_id, []).append(link.message_id)

    return [
        Send("update_subagent", 
            {
                'existing' : {item[0]: state.existing[item[0]]},
                'messages' : [msg for msg in state.messages if msg.id in item[1]],
                'plan' : state.plan
            }) for item in relevant_for_update_links_by_user_id.items() if item[0] in state.existing
    ]

def run_update_subgagent(state: MainState) -> MainState:
    
    sub_state = {"messages" : state.messages,
                 "existing" : state.existing,
                 "reasoning_summary_for_update" : state.plan.reasoning_summary_for_update}
    result = update_subgraph.invoke(sub_state)
    # need to make sure the custom reducer is good enough for updating existing profiles.
    return {
        "existing": result["existing"]
    }

# ----------------------------
# 5. Parent Graph
# ----------------------------


def route_after_planner(state: MainState) -> list[Literal["extract_subagent", "__end__"] | Send]:
    destinations = []

    plan = state.plan
    if plan.relevant_for_create_links:
        destinations.append("extract_subagent")
    if plan.relevant_for_update_links:
        destinations.extend(fan_out_updates(state))
    if not destinations:
        return ["__end__"]
    else: 
        return destinations

parent_builder = StateGraph(MainState)

parent_builder.add_node("planner", planner_node)
parent_builder.add_node("extract_subagent", run_extract_subgagent)
parent_builder.add_node("update_subagent", run_update_subgagent)


parent_builder.add_edge(START, "planner")
parent_builder.add_conditional_edges("planner", route_after_planner)
parent_builder.add_edge("extract_subagent", END)
parent_builder.add_edge("update_subagent", END)

config = {"configurable": {"thread_id": "1"}}
memory = InMemorySaver()
graph = parent_builder.compile(checkpointer=memory)
