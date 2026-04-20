from operator import add
from typing import Annotated, Literal, Optional

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class PatchOp(BaseModel):
    op: Literal["add", "remove", "replace"]
    path: str
    value: Optional[str | list[str]] = None

class PatchProposal(BaseModel):
    target_id: str = Field(description="ID of the object to update")
    patches: list[PatchOp] = Field(description="JSON Patch-style operations")

class PatchProposalList(BaseModel):
    items: list[PatchProposal] = Field(default_factory=list)

class UserProfile(BaseModel):
    name: Optional[str] = Field(default=None, description="User's full name")
    company: Optional[str] = Field(default=None, description="Company the user works at")
    role: Optional[str] = Field(default=None, description="User's job title or role")
    location: Optional[str] = Field(default=None, description="Where the user is based")
    interests: list[str] = Field(default_factory=list, description="Important interests or topics the user cares about")

class UserProfileList(BaseModel):
    items: list[UserProfile] = Field(default_factory=list)

# Legacy planner contract from the earlier count-and-target architecture.
# Keep it until graphv3.py is switched over to MessageSelectionOutput.
class PlannerOutput(BaseModel):
    target_ids_to_update: list[str]
    reasoning_summary: str
    new_person_count: int

class UpdateLink(BaseModel):
    """Message-to-existing-profile mapping for the update branch.

    Each UpdateLink says:
    - which human message contains update-relevant information
    - which existing user profile ids should be updated from that message
    """
    message_id: str = Field(description="ID of the human message relevant for updating existing user profiles.")
    user_profile_ids: list[str] = Field(
        default_factory=list,
        description="List of existing user profile IDs that should be updated from that single human message.",
    )

class CreateLink(BaseModel):
    """Message-to-create-count mapping for the create branch.

    Each CreateLink says:
    - which human message contains create-relevant information
    - how many new people are mentioned in that message
    """
    message_id: str = Field(description="ID of the human message relevant for creating new user profiles.")
    new_person_count: int = Field(
        description="Number of new people mentioned in that single human message.",
    )

class MessageSelectionOutput(BaseModel):
    """Planner output for the newer message-selection architecture.

    This schema does three jobs:
    - summarize the create-side context for the extract subagent
    - summarize the update-side context for the update subagent
    - point each branch to the exact messages it should use

    The create branch consumes:
    - reasoning_summary_for_create
    - relevant_for_create_links

    The update branch consumes:
    - reasoning_summary_for_update
    - relevant_for_update_links
    """
    reasoning_summary_for_create: str = Field(
        description="Short summary of the create-side information across all relevant messages. This will help the extraction subagent focus on what new people need to be extracted."
    )
    reasoning_summary_for_update: str = Field(
        description="Short summary of the update-side information across all relevant messages. This will help the update subagent focus on what existing profiles need to be updated."
    )
    relevant_for_create_links: list[CreateLink] = Field(
        default_factory=list,
        description="List of links from human message IDs to the number of new user profiles mentioned in those messages.",
    )
    relevant_for_update_links: list[UpdateLink] = Field(
        default_factory=list,
        description="List of links from human message IDs to the existing user profile IDs that should be updated from those messages.",
    )


# Transitional legacy state from the earlier single-state architecture.
# Keep it only until graphv2.py is fully refactored to use MainState,
# ExtractAgentState, and UpdateAgentState.
class ExtractionState(BaseModel):
    messages: Annotated[list[BaseMessage], add]
    existing: dict[str, UserProfile] = Field(default_factory=dict)
    candidate: dict[str, UserProfile] = Field(default_factory=dict)
    errors: dict[str, list[str]] = Field(default_factory=dict)
    attempts: int = 0
    patches: list[PatchProposal] = Field(default_factory=list)
    plan: PlannerOutput | None = None

class MainState(BaseModel):
    messages: Annotated[list[BaseMessage], add]
    existing: dict[str, UserProfile] = Field(default_factory=dict)
    plan: PlannerOutput | None = None

class ExtractAgentState(MainState):
    pass

class UpdateAgentState(MainState):
    candidate: dict[str, UserProfile] = Field(default_factory=dict)
    errors: dict[str, list[str]] = Field(default_factory=dict)
    attempts: int = 0
    patches: list[PatchProposal] = Field(default_factory=list)

    
    
