from pathlib import Path
import sys
from threading import Lock
from uuid import UUID

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


class PromptRoutingLLM:
    """Return deterministic structured outputs without relying on branch order."""

    def __init__(
        self,
        subjects: SubjectBucketList,
        profiles_by_label: dict[str, UserProfile] | None = None,
        patches_by_id: dict[str, PatchProposalList] | None = None,
    ):
        self.subjects = subjects
        self.profiles_by_label = profiles_by_label or {}
        self.patches_by_id = patches_by_id or {}
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
                if schema is UserProfile:
                    for label, profile in outer.profiles_by_label.items():
                        if f"new subject labeled:\n{label}" in prompt:
                            return profile
                if schema is PatchProposalList:
                    for user_id, patches in outer.patches_by_id.items():
                        if f"Obj_id = {user_id}:" in prompt:
                            return patches
                raise AssertionError(
                    f"No fake output configured for schema={schema.__name__}."
                )

        return StructuredOutput()

    def prompts_for(self, schema):
        return [prompt for called_schema, prompt in self.calls if called_schema is schema]


def compile_parent_graph():
    return graphv3.parent_builder.compile()


def replace_field(user_id: str, path: str, value: str) -> PatchProposalList:
    return PatchProposalList(
        items=[
            PatchProposal(
                target_id=user_id,
                patches=[PatchOp(op="replace", path=path, value=value)],
            )
        ]
    )


def prompt_containing(prompts: list[str], marker: str) -> str:
    matches = [prompt for prompt in prompts if marker in prompt]
    assert len(matches) == 1
    return matches[0]


def assert_contains_only_subject_evidence(
    prompt: str,
    shared: HumanMessage,
    included: HumanMessage,
    excluded: list[HumanMessage],
) -> None:
    assert shared.content in prompt
    assert included.content in prompt
    for message in excluded:
        assert message.content not in prompt


def test_no_subjects_completes_without_branch_work(monkeypatch):
    profile = UserProfile(name="John", location="London")
    fake_llm = PromptRoutingLLM(SubjectBucketList())
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = compile_parent_graph().invoke(
        MainState(
            messages=[HumanMessage(id="hm_001", content="It rained yesterday.")],
            existing={"user_john": profile},
        )
    )

    assert result["existing"] == {"user_john": profile}
    assert result["subjects"] == SubjectBucketList()
    assert [schema for schema, _ in fake_llm.calls] == [SubjectBucketList]


def test_create_only_batch_merges_distinct_profiles_with_isolated_evidence(
    monkeypatch,
):
    shared = HumanMessage(id="hm_shared", content="Lucia introduced me to Maria.")
    lucia_message = HumanMessage(
        id="hm_lucia",
        content="Lucia is a lawyer from Lima.",
    )
    maria_message = HumanMessage(
        id="hm_maria",
        content="Maria is an engineer from Quito.",
    )
    lucia_repeat = HumanMessage(
        id="hm_lucia_repeat",
        content="Lucia enjoys football.",
    )
    subjects = SubjectBucketList(
        items=[
            new_subject("Lucia", ["hm_shared", "hm_lucia", "hm_lucia_repeat"]),
            new_subject("Maria", ["hm_shared", "hm_maria"]),
        ]
    )
    lucia = UserProfile(
        name="Lucia",
        role="Lawyer",
        location="Lima",
        interests=["football"],
    )
    maria = UserProfile(name="Maria", role="Engineer", location="Quito")
    fake_llm = PromptRoutingLLM(
        subjects,
        profiles_by_label={"Lucia": lucia, "Maria": maria},
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = compile_parent_graph().invoke(
        MainState(messages=[shared, lucia_message, maria_message, lucia_repeat])
    )

    assert sorted(
        profile.name for profile in result["existing"].values()
    ) == ["Lucia", "Maria"]
    created_ids = list(result["existing"])
    assert len(created_ids) == 2
    assert len(set(created_ids)) == 2
    for created_id in created_ids:
        UUID(created_id)

    extraction_prompts = fake_llm.prompts_for(UserProfile)
    lucia_prompt = prompt_containing(extraction_prompts, "new subject labeled:\nLucia")
    maria_prompt = prompt_containing(extraction_prompts, "new subject labeled:\nMaria")
    assert_contains_only_subject_evidence(
        lucia_prompt,
        shared,
        lucia_message,
        [maria_message],
    )
    assert lucia_repeat.content in lucia_prompt
    assert_contains_only_subject_evidence(
        maria_prompt,
        shared,
        maria_message,
        [lucia_message, lucia_repeat],
    )
    assert fake_llm.prompts_for(PatchProposalList) == []


def test_update_only_batch_merges_real_update_and_noop_with_isolated_evidence(
    monkeypatch,
):
    john = UserProfile(name="John", location="London")
    lucia = UserProfile(name="Lucia", role="Lawyer", location="Lima")
    shared = HumanMessage(id="hm_shared", content="I spoke with John and Lucia.")
    john_message = HumanMessage(id="hm_john", content="John moved to Miami.")
    lucia_message = HumanMessage(
        id="hm_lucia",
        content="Lucia told me about her day.",
    )
    subjects = SubjectBucketList(
        items=[
            existing_subject("John", ["hm_shared", "hm_john"], "user_john"),
            existing_subject("Lucia", ["hm_shared", "hm_lucia"], "user_lucia"),
        ]
    )
    fake_llm = PromptRoutingLLM(
        subjects,
        patches_by_id={
            "user_john": replace_field("user_john", "/location", "Miami"),
            "user_lucia": PatchProposalList(),
        },
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = compile_parent_graph().invoke(
        MainState(
            messages=[shared, john_message, lucia_message],
            existing={"user_john": john, "user_lucia": lucia},
        )
    )

    assert result["existing"] == {
        "user_john": UserProfile(name="John", location="Miami"),
        "user_lucia": lucia,
    }
    update_prompts = fake_llm.prompts_for(PatchProposalList)
    john_prompt = prompt_containing(update_prompts, "Obj_id = user_john:")
    lucia_prompt = prompt_containing(update_prompts, "Obj_id = user_lucia:")
    assert_contains_only_subject_evidence(
        john_prompt,
        shared,
        john_message,
        [lucia_message],
    )
    assert_contains_only_subject_evidence(
        lucia_prompt,
        shared,
        lucia_message,
        [john_message],
    )
    assert fake_llm.prompts_for(UserProfile) == []


def test_mixed_batch_preserves_every_create_and_update_result(monkeypatch):
    john = UserProfile(name="John", location="London")
    ana = UserProfile(name="Ana", role="Designer", location="Madrid")
    shared = HumanMessage(
        id="hm_shared",
        content="John and Ana introduced me to Lucia and Maria.",
    )
    john_message = HumanMessage(id="hm_john", content="John moved to Miami.")
    ana_message = HumanMessage(id="hm_ana", content="Ana described her project.")
    lucia_message = HumanMessage(id="hm_lucia", content="Lucia is a lawyer.")
    maria_message = HumanMessage(id="hm_maria", content="Maria is an engineer.")
    subjects = SubjectBucketList(
        items=[
            existing_subject("John", ["hm_shared", "hm_john"], "user_john"),
            new_subject("Lucia", ["hm_shared", "hm_lucia"]),
            existing_subject("Ana", ["hm_shared", "hm_ana"], "user_ana"),
            new_subject("Maria", ["hm_shared", "hm_maria"]),
        ]
    )
    lucia = UserProfile(name="Lucia", role="Lawyer")
    maria = UserProfile(name="Maria", role="Engineer")
    fake_llm = PromptRoutingLLM(
        subjects,
        profiles_by_label={"Lucia": lucia, "Maria": maria},
        patches_by_id={
            "user_john": replace_field("user_john", "/location", "Miami"),
            "user_ana": PatchProposalList(),
        },
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = compile_parent_graph().invoke(
        MainState(
            messages=[
                shared,
                john_message,
                ana_message,
                lucia_message,
                maria_message,
            ],
            existing={"user_john": john, "user_ana": ana},
        )
    )

    assert result["existing"]["user_john"] == UserProfile(
        name="John",
        location="Miami",
    )
    assert result["existing"]["user_ana"] == ana
    created = {
        user_id: profile
        for user_id, profile in result["existing"].items()
        if user_id not in {"user_john", "user_ana"}
    }
    assert sorted(profile.name for profile in created.values()) == ["Lucia", "Maria"]
    assert len(created) == 2
    assert len(set(created)) == 2
    assert all(user_id not in {"user_john", "user_ana"} for user_id in created)

    prompts_by_schema = {
        UserProfile: fake_llm.prompts_for(UserProfile),
        PatchProposalList: fake_llm.prompts_for(PatchProposalList),
    }
    branch_markers = {
        UserProfile: {
            "new subject labeled:\nLucia": (
                lucia_message,
                [john_message, ana_message, maria_message],
            ),
            "new subject labeled:\nMaria": (
                maria_message,
                [john_message, ana_message, lucia_message],
            ),
        },
        PatchProposalList: {
            "Obj_id = user_john:": (
                john_message,
                [ana_message, lucia_message, maria_message],
            ),
            "Obj_id = user_ana:": (
                ana_message,
                [john_message, lucia_message, maria_message],
            ),
        },
    }
    for schema, branches in branch_markers.items():
        for marker, (included, excluded) in branches.items():
            prompt = prompt_containing(prompts_by_schema[schema], marker)
            assert_contains_only_subject_evidence(prompt, shared, included, excluded)
