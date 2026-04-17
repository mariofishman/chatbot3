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

class PlannerOutput(BaseModel):
    target_ids_to_update: list[str]
    reasoning_summary: str
    new_person_count: int

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
    # messages: Annotated[list[BaseMessage], add]
    # existing: dict[str, UserProfile] = Field(default_factory=dict)
    # plan: PlannerOutput | None = None
    pass

class UpdateAgentState(MainState):
    # messages: Annotated[list[BaseMessage], add]
    # existing: dict[str, UserProfile] = Field(default_factory=dict)
    # plan: PlannerOutput | None = None
    candidate: dict[str, UserProfile] = Field(default_factory=dict)
    errors: dict[str, list[str]] = Field(default_factory=dict)
    attempts: int = 0
    patches: list[PatchProposal] = Field(default_factory=list)

    
    
