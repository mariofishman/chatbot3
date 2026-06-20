from pathlib import Path
import sys
from threading import Lock

from langchain_core.messages import HumanMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import (
    MainState,
    PatchOp,
    PatchProposal,
    PatchProposalList,
    SubjectBucket,
    SubjectBucketList,
    UserProfile,
)


def new_subject(label: str, message_ids: list[str]) -> SubjectBucket:
    return SubjectBucket(
        subject_label=label,
        message_ids=message_ids,
        classification="new",
    )


def existing_subject(
    label: str,
    message_ids: list[str],
    user_id: str,
) -> SubjectBucket:
    return SubjectBucket(
        subject_label=label,
        message_ids=message_ids,
        candidate_existing_id=user_id,
        classification="existing",
    )


def replace_field(user_id: str, path: str, value) -> PatchProposalList:
    return PatchProposalList(
        items=[
            PatchProposal(
                target_id=user_id,
                patches=[PatchOp(op="replace", path=path, value=value)],
            )
        ]
    )


class DuplicateBoundaryLLM:
    """Return duplicate planner output and deterministic branch responses."""

    def __init__(
        self,
        subjects: SubjectBucketList,
        patches_by_id: dict[str, PatchProposalList] | None = None,
        profiles_by_label: dict[str, UserProfile] | None = None,
    ):
        self.subjects = subjects
        self.patches_by_id = patches_by_id or {}
        self.profiles_by_label = profiles_by_label or {}
        self.calls = []
        self._lock = Lock()

    def with_structured_output(self, schema):
        outer = self

        class StructuredOutput:
            def invoke(self, messages):
                prompt = messages[0].content
                with outer._lock:
                    outer.calls.append((schema, prompt))

                if schema is SubjectBucketList:
                    return outer.subjects
                if schema is PatchProposalList:
                    for user_id, patches in outer.patches_by_id.items():
                        if f"Obj_id = {user_id}:" in prompt:
                            return patches
                if schema is UserProfile:
                    for label, profile in outer.profiles_by_label.items():
                        if f"new subject labeled:\n{label}" in prompt:
                            return profile
                raise AssertionError(f"Unexpected schema: {schema.__name__}")

        return StructuredOutput()

    def prompts_for(self, schema):
        return [prompt for called_schema, prompt in self.calls if called_schema is schema]


def compile_parent_graph():
    return graphv3.parent_builder.compile()


def test_subject_planner_merges_duplicate_existing_ids_into_one_clean_bucket(
    monkeypatch,
):
    subjects = SubjectBucketList(
        items=[
            existing_subject("John", ["hm_001"], "user_john"),
            existing_subject("John", ["hm_002"], "user_john"),
        ]
    )
    fake_llm = DuplicateBoundaryLLM(subjects)
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = graphv3.subject_planner_node(
        MainState(
            messages=[
                HumanMessage(id="hm_001", content="John moved to Miami."),
                HumanMessage(id="hm_002", content="John became a director."),
            ],
            existing={"user_john": UserProfile(name="John")},
        )
    )

    assert result == {
        "subjects": SubjectBucketList(
            items=[existing_subject("John", ["hm_001", "hm_002"], "user_john")]
        )
    }


def test_duplicate_existing_ids_produce_one_update_branch_with_merged_messages(
    monkeypatch,
):
    subjects = SubjectBucketList(
        items=[
            existing_subject("John", ["hm_001"], "user_john"),
            existing_subject("John", ["hm_002"], "user_john"),
        ]
    )
    john = UserProfile(name="John", location="London")
    fake_llm = DuplicateBoundaryLLM(
        subjects,
        patches_by_id={
            "user_john": replace_field("user_john", "/location", "Miami")
        },
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = compile_parent_graph().invoke(
        MainState(
            messages=[
                HumanMessage(id="hm_001", content="John moved to Miami."),
                HumanMessage(id="hm_002", content="John became a director."),
            ],
            existing={"user_john": john},
        )
    )

    assert result["subjects"] == SubjectBucketList(
        items=[existing_subject("John", ["hm_001", "hm_002"], "user_john")]
    )
    assert result["existing"] == {
        "user_john": UserProfile(name="John", location="Miami")
    }
    update_prompts = fake_llm.prompts_for(PatchProposalList)
    assert len(update_prompts) == 1
    assert "John moved to Miami." in update_prompts[0]
    assert "John became a director." in update_prompts[0]


def test_duplicate_new_labels_are_not_frozen_as_duplicates_yet(monkeypatch):
    subjects = SubjectBucketList(
        items=[
            new_subject("John", ["hm_001"]),
            new_subject("John", ["hm_002"]),
        ]
    )
    fake_llm = DuplicateBoundaryLLM(
        subjects,
        profiles_by_label={
            "John": UserProfile(name="John"),
        },
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = graphv3.subject_planner_node(
        MainState(
            messages=[
                HumanMessage(id="hm_001", content="I met an old friend named John."),
                HumanMessage(id="hm_002", content="I met a young neighbor named John."),
            ]
        )
    )

    assert result == {"subjects": subjects}
