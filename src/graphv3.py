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

from state import MainState, ExtractAgentState, UpdateAgentState, UserProfile, UserProfileList, MessageSelectionOutput, PatchProposalList

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
    # Expect resume payload in UserProfileList JSON shape.
    # Example:
    # {
    #   "items": [
    #     {
    #       "name": "Lucia Romero",
    #       "company": None,
    #       "role": "Startup Lawyer",
    #       "location": "Lima",
    #       "interests": [],
    #     }
    #   ]
    # }
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
class UpdateAgentState(BaseModel):
    messages: Annotated[list[BaseMessage], add]
    existing: Annotated[dict[str, UserProfile], merge_profiles] = Field(default_factory=dict)
    reasoning_summary_for_update: str
    candidate: dict[str, dict] = Field(default_factory=dict)
    errors: dict[str, list[str]] = Field(default_factory=dict)
    attempts: int = 0
    patches: list[PatchProposal] = Field(default_factory=list)
"""

def update_patches(state: UpdateAgentState) -> UpdateAgentState:
    """Generate patch proposals for the filtered update branch.

    This node is the update-side equivalent of the create extractor.
    It should read only the already-filtered update context prepared by the
    parent wrapper for one target profile:

    - `state.messages`: only the update-relevant messages for one target user
    - `state.existing`: only the single target profile for that user
    - `state.reasoning_summary_for_update`: shared planner-side update summary
      used only as supporting context

    Its only job is to call the model and produce a `PatchProposalList`
    describing how that single target profile should be updated.

    It should not apply patches, validate results, or commit changes.
    """
    target_existing = state.existing
    if len(target_existing) != 1:
        raise ValueError(
            "update_patches() expects exactly one target profile in state.existing."
        )
    formatted_messages = format_messages(state.messages)
    formatted_schema = format_string_from_schema(UserProfile)
    formatted_existing = "\n".join(
        [
            f"Obj_id = {k}:\n{format_string_from_user_profile(v)}\n"
            + "-" * 60
            + "\n"
            for k, v in target_existing.items()
        ]
    )

    system_prompt = f"""
You are preparing JSON patch proposals for one existing user profile.

Your job is only to propose patch operations for the target profile shown
below. Do not rewrite the whole object. Do not apply the patch yourself.
Use the existing profile as the baseline truth.

The update reasoning summary may mention other users or unrelated updates.
Ignore any part of that summary that is not relevant to the single target
profile shown below. Use the summary only as supporting background. The
primary sources of truth are:
- the single target profile shown below
- the filtered messages shown below

Return output that matches the PatchProposalList schema exactly.

Rules:
- Use only information explicitly stated or strongly implied in the messages.
- Do not guess or invent facts.
- Do not include fields that do not need to change.
- Only return patch operations for fields that should be added, removed, or replaced.
- Each PatchProposal must target exactly the one existing object shown below.
- Do not invent new target IDs.
- Every patch path must correspond to a valid field in the UserProfile schema.
- Every patch value must be compatible with the field meaning and type in the schema.
- If the messages do not support any real change for this profile, return an empty PatchProposalList.

USERPROFILE SCHEMA:
{formatted_schema}

TARGET EXISTING PROFILE:
{formatted_existing}

SUPPORTING UPDATE SUMMARY:
{state.reasoning_summary_for_update}

RELEVANT MESSAGE(S) FOR THIS PROFILE:
{formatted_messages}
"""

    structured_llm = llm.with_structured_output(PatchProposalList)
    result = structured_llm.invoke([SystemMessage(system_prompt)])
    return {"patches": result.items}

def apply_patch(state: UpdateAgentState) -> UpdateAgentState:
    """Apply proposed patches into update-local candidate state.

    This node should deterministically apply the patch proposals created by
    `update_patches` to the single target profile in `state.existing` and
    write the patched raw intermediate result into update-local `candidate`
    state.

    It should enforce the one-user contract explicitly and fail clearly if
    any patch proposal targets a different user id than the one carried in
    `state.existing`.

    It should not ask the model for new patches, eagerly reconstruct the
    final `UserProfile`, validate the patched profile semantically, or merge
    anything into top-level parent state.

    The key handoff is:
    - `apply_patch()` returns raw patched dict data in `candidate`
    - `validate()` is responsible for attempting `UserProfile(**target_data)`
      and recording any reconstruction/type errors into `state.errors`
    """
    if len(state.existing) != 1:
        raise ValueError(
            "apply_patch() expects exactly one target profile in state.existing."
        )
    if not state.patches:
        raise ValueError(
            "apply_patch() expects at least one PatchProposal in state.patches."
        )

    target_id, target_profile = next(iter(state.existing.items()))
    target_data = target_profile.model_dump()

    def decode_pointer_token(token: str) -> str:
        return token.replace("~1", "/").replace("~0", "~")

    def set_value(container, key, value):
        if isinstance(container, list):
            if key == "-":
                container.append(value)
            else:
                index = int(key)
                if index == len(container):
                    container.append(value)
                else:
                    container[index] = value
        else:
            container[key] = value

    def remove_value(container, key):
        if isinstance(container, list):
            del container[int(key)]
        else:
            if key not in container:
                raise KeyError(f"Patch remove path does not exist: {key}")
            container.pop(key)

    def resolve_parent(doc: dict, path: str):
        if not path.startswith("/"):
            raise ValueError(f"Patch path must start with '/': {path}")

        tokens = [decode_pointer_token(token) for token in path.lstrip("/").split("/")]
        if not tokens or tokens == [""]:
            raise ValueError("Patch path must point to a concrete field.")

        current = doc
        for token in tokens[:-1]:
            if isinstance(current, list):
                current = current[int(token)]
            else:
                if token not in current:
                    raise KeyError(f"Patch path does not exist: {path}")
                current = current[token]

        return current, tokens[-1]

    for proposal in state.patches:
        if proposal.target_id != target_id:
            raise ValueError(
                f"apply_patch() received patch target_id={proposal.target_id}, "
                f"but current target profile is {target_id}."
            )

        for patch in proposal.patches:
            parent, key = resolve_parent(target_data, patch.path)

            if patch.op in {"add", "replace"}:
                set_value(parent, key, patch.value)
            elif patch.op == "remove":
                remove_value(parent, key)
            else:
                raise ValueError(f"Unsupported patch op: {patch.op}")

    return {"candidate": {target_id: target_data}}

def validate(state: UpdateAgentState) -> UpdateAgentState:
    """Validate patched candidates and record update-local errors.

    This node should inspect the candidate profiles produced by
    `apply_patch`, reconstruct/validate the raw candidate dicts as final
    `UserProfile` objects, and store any errors in update-local state.

    It should not generate new patches or commit final results.
    """
    candidate = state.candidate or {}

    if len(candidate) != 1:
        raise ValueError(
            "validate() expects exactly one candidate profile in state.candidate."
        )

    target_id, candidate_data = next(iter(candidate.items()))

    if not isinstance(target_id, str) or not target_id.strip():
        raise ValueError("Candidate key must be a non-empty user id string.")

    if not isinstance(candidate_data, dict):
        raise ValueError("Candidate value must be a raw dict payload.")

    try:
        UserProfile(**candidate_data)
    except ValidationError as e:
        return {
            "errors": {
                target_id: [
                    f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
                    if err.get("loc")
                    else err["msg"]
                    for err in e.errors()
                ]
            }
        }

    return {"errors": {}}

def route_patches(state: UpdateAgentState) -> Literal["patch", "commit", "human_repair"]:
    """Choose whether the update branch should repair or finish.

    This routing function should inspect update-local validation results and
    decide between:

    - `"patch"` when there are validation errors that still need repair
    - `"commit"` when the candidate profiles are valid and ready to return
    - `"human_repair"` when validation errors remain after the retry limit

    It should not modify state directly. A separate node should handle any
    interrupt-based human handoff once the retry limit has been exhausted.
    """
    max_patch_attempts = 3

    if not state.errors:
        return "commit"
    if state.attempts >= max_patch_attempts:
        return "human_repair"
    return "patch"


def human_repair(state: UpdateAgentState) -> UpdateAgentState:
    """Pause the update loop and ask a human for corrective patches.

    This node is reached only after validation errors remain once the patch
    retry limit has been exhausted. It preserves the current update-local
    state and asks the human to provide corrective `PatchProposalList` data.
    """
    if len(state.existing) != 1:
        raise ValueError(
            "human_repair() expects exactly one target profile in state.existing."
        )
    if len(state.candidate) != 1:
        raise ValueError(
            "human_repair() expects exactly one raw candidate profile in state.candidate."
        )
    if not state.errors:
        raise ValueError(
            "human_repair() expects non-empty state.errors after failed validation."
        )

    target_id, target_profile = next(iter(state.existing.items()))
    candidate_id, candidate_data = next(iter(state.candidate.items()))

    if candidate_id != target_id:
        raise ValueError(
            f"human_repair() received candidate_id={candidate_id}, "
            f"but current target profile is {target_id}."
        )

    payload = interrupt(
        {
            "message": (
                "The maximum number of patch repair attempts was reached. "
                "Please return corrective JSON patch proposals for this one target profile."
            ),
            "target_id": target_id,
            "existing_profile": target_profile.model_dump(),
            "failed_candidate": candidate_data,
            "errors": state.errors,
            "expected_format": {
                "items": [
                    {
                        "target_id": target_id,
                        "patches": [
                            {
                                "op": "replace",
                                "path": "/interests",
                                "value": ["metals", "AI hiring"],
                            }
                        ],
                    }
                ]
            },
        }
    )

    while True:
        try:
            validated_result = PatchProposalList.model_validate(payload)
            if not validated_result.items:
                raise ValueError(
                    "At least one PatchProposal must be provided for human repair."
                )
            if any(proposal.target_id != target_id for proposal in validated_result.items):
                raise ValueError(
                    "All human repair PatchProposals must target the current user id."
                )
            break
        except (ValidationError, ValueError) as e:
            payload = interrupt(
                {
                    "message": (
                        "The payload did not match the expected PatchProposalList JSON shape. "
                        "Please try again."
                    ),
                    "errors": e.errors() if isinstance(e, ValidationError) else [str(e)],
                    "expected_format": {
                        "items": [
                            {
                                "target_id": target_id,
                                "patches": [
                                    {
                                        "op": "replace",
                                        "path": "/interests",
                                        "value": ["metals", "AI hiring"],
                                    }
                                ],
                            }
                        ]
                    },
                }
            )

    return {
        "patches": validated_result.items,
        "errors": {},
        "attempts": state.attempts,
    }

def patch(state: UpdateAgentState) -> UpdateAgentState:
    """Repair invalid candidates using validation feedback.

    This node should use the validation errors recorded in update-local state
    to ask the model for a corrective patching step, or otherwise repair the
    invalid candidate profiles.

    Its output should prepare the branch for another deterministic validation
    pass.
    """
    if len(state.existing) != 1:
        raise ValueError(
            "patch() expects exactly one target profile in state.existing."
        )
    if len(state.candidate) != 1:
        raise ValueError(
            "patch() expects exactly one raw candidate profile in state.candidate."
        )
    if not state.errors:
        raise ValueError(
            "patch() expects non-empty state.errors after failed validation."
        )

    target_id, target_profile = next(iter(state.existing.items()))
    candidate_id, candidate_data = next(iter(state.candidate.items()))

    if candidate_id != target_id:
        raise ValueError(
            f"patch() received candidate_id={candidate_id}, "
            f"but current target profile is {target_id}."
        )

    if not isinstance(candidate_data, dict):
        raise ValueError("patch() expects candidate payload to be a raw dict.")

    formatted_messages = format_messages(state.messages)
    formatted_schema = format_string_from_schema(UserProfile)
    formatted_existing = format_string_from_user_profile(target_profile)
    formatted_candidate = "\n".join([f"{k} : {v}" for k, v in candidate_data.items()])
    formatted_errors = "\n".join(
        [f"{profile_id}: {', '.join(profile_errors)}" for profile_id, profile_errors in state.errors.items()]
    )

    system_prompt = f"""
You are repairing JSON Patch-style updates for one existing user profile.

Return a PatchProposalList that fixes the current failed raw candidate.

Rules:
- Work on exactly one target profile id: {target_id}
- Use the original existing profile as baseline context only
- Use the failed raw candidate and validation errors as the main repair signal
- Produce only patch operations needed to fix the validation errors
- Each returned patch must directly address at least one listed validation error
- Prefer the smallest corrective patch set
- Preserve valid fields in the failed candidate unless an error requires changing them
- Do not repeat unchanged bad values
- Do not invent facts not supported by the messages
- Return output that matches the PatchProposalList schema exactly

TARGET USERPROFILE SCHEMA:
{formatted_schema}

ORIGINAL EXISTING PROFILE:
Obj_id = {target_id}
{formatted_existing}

FAILED RAW CANDIDATE:
Obj_id = {candidate_id}
{formatted_candidate}

VALIDATION ERRORS:
{formatted_errors}

SUPPORTING UPDATE SUMMARY:
{state.reasoning_summary_for_update}

UPDATE-RELEVANT MESSAGES:
{formatted_messages}
"""

    structured_llm = llm.with_structured_output(PatchProposalList)
    result = structured_llm.invoke([SystemMessage(system_prompt)])
    return {"patches": result.items, "attempts": state.attempts + 1}

def commit(state: UpdateAgentState) -> UpdateAgentState:
    """Return committed update results from the update subgraph.

    This node should take the validated update-local candidates and return the
    final one-user `existing` update slice that the parent graph can merge
    into top-level `MainState.existing` through the reducer.

    It should not return the full parent state, only the committed update
    slice for the selected target profiles.
    """
    if len(state.existing) != 1:
        raise ValueError(
            "commit() expects exactly one target profile in state.existing."
        )
    if len(state.candidate) != 1:
        raise ValueError(
            "commit() expects exactly one raw candidate profile in state.candidate."
        )
    if state.errors:
        raise ValueError(
            "commit() expects empty state.errors after successful validation."
        )

    target_id, _ = next(iter(state.existing.items()))
    candidate_id, candidate_data = next(iter(state.candidate.items()))

    if candidate_id != target_id:
        raise ValueError(
            f"commit() received candidate_id={candidate_id}, "
            f"but current target profile is {target_id}."
        )
    if not isinstance(candidate_data, dict):
        raise ValueError("commit() expects candidate payload to be a raw dict.")

    validated_profile = UserProfile(**candidate_data)
    return {"existing": {target_id: validated_profile}}


update_builder = StateGraph(UpdateAgentState)

update_builder.add_node("update_patches", update_patches)
update_builder.add_node("apply_patch", apply_patch)
update_builder.add_node("validate", validate)
update_builder.add_node("patch", patch)
update_builder.add_node("human_repair", human_repair)
update_builder.add_node("commit", commit)

update_builder.add_edge(START, "update_patches")
update_builder.add_edge("update_patches", "apply_patch")
update_builder.add_edge("apply_patch", "validate")
update_builder.add_conditional_edges("validate", route_patches)
update_builder.add_edge("patch", "validate")
update_builder.add_edge("human_repair", "apply_patch")
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

Your job is only to decide which human messages are relevant for:
1. creating or extracting new user profiles
2. updating existing user profiles

You are not extracting profile fields.
You are not producing patch operations.
You are not validating data.
You are only planning the next actions.

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
- A profile should be selected for update even if only one field changes.
- If a message contains update information, add an item to relevant_for_update_links with the message_id and the correct user_profile_ids.
- If a message contains create information, add an item to relevant_for_create_links with the message_id and the number of new people mentioned in that message.
- The same message ID may appear in relevant_for_create_links and also inside relevant_for_update_links.
- If a message clearly introduces a different person who is not one of the existing profiles, treat that as create-side evidence.
- Do not map a newly mentioned person onto an existing profile unless the messages provide clear evidence they are the same person.
- Shared facts such as company, role, or location are not enough by themselves to conclude that a newly named person is actually an existing profile.
- When in doubt between "update existing" and "create new", prefer create-side selection rather than risking an incorrect overwrite.
- Use only information explicitly stated or strongly implied in the conversation.
- Do not guess.
- Do not invent IDs.
- Do not invent existing user profile IDs.
- Only use user_profile_ids that are present in the provided existing profiles.
- Keep reasoning summaries short, factual, and high level.

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
