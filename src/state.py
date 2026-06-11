from operator import add
from typing import Annotated, Literal, Optional

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, model_validator


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

class SubjectBucket(BaseModel):
    """One batch-local person identified before create/update planning."""

    subject_label: str = Field(
        min_length=1,
        description="Best available label for the detected person.",
    )
    message_ids: list[str] = Field(
        min_length=1,
        description="IDs of all messages in the current batch that refer to this person."
    )
    candidate_existing_id: str | None = Field(
        default=None,
        min_length=1,
        description="Chosen existing profile ID when this person is classified as existing.",
    )
    classification: Literal["existing", "new"]

    @model_validator(mode="after")
    def validate_existing_candidate_contract(self):
        if self.classification == "existing" and self.candidate_existing_id is None:
            raise ValueError(
                "candidate_existing_id must be set when classification is 'existing'."
            )
        if self.classification == "new" and self.candidate_existing_id is not None:
            raise ValueError(
                "candidate_existing_id must be None when classification is 'new'."
            )
        return self

class SubjectBucketList(BaseModel):
    items: list[SubjectBucket] = Field(default_factory=list)

def merge_profiles(
    existing: dict[str, UserProfile] | None,
    new: dict[str, UserProfile] | None,
) -> dict[str, UserProfile]:
    """Merge whole UserProfile objects by user_id for parent state.

    This reducer operates only at the dict level:
    - keep existing profiles whose ids are not present in `new`
    - add brand-new ids from `new`
    - replace the whole profile when the same id appears in both inputs

    It does not merge fields inside a UserProfile. Field-level updating belongs
    to the update subgraph before committed profiles are returned here.
    """
    existing_profiles = existing or {}
    new_profiles = new or {}
    merged_profiles = {**existing_profiles, **new_profiles}
    return merged_profiles
class MainState(BaseModel):
    messages: Annotated[list[BaseMessage], add]
    existing: Annotated[dict[str, UserProfile], merge_profiles] = Field(default_factory=dict)
    subjects: SubjectBucketList = Field(default_factory=SubjectBucketList)


class ExtractAgentState(BaseModel):
    subject: SubjectBucket
    messages: Annotated[list[BaseMessage], add]
    existing: Annotated[dict[str, UserProfile], merge_profiles] = Field(default_factory=dict)

class UpdateAgentState(BaseModel):
    messages: Annotated[list[BaseMessage], add]
    existing: Annotated[dict[str, UserProfile], merge_profiles] = Field(default_factory=dict)
    candidate: dict[str, dict] = Field(default_factory=dict)
    errors: dict[str, list[str]] = Field(default_factory=dict)
    attempts: int = 0
    patches: list[PatchProposal] = Field(default_factory=list)
    

    
