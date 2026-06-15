from pathlib import Path
import sys
from threading import Lock

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

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


def existing_subject(label: str, message_id: str, user_id: str) -> SubjectBucket:
    return SubjectBucket(
        subject_label=label,
        message_ids=[message_id],
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


class ParallelRepairLLM:
    """Route update outputs by target and repair-prompt content."""

    def __init__(self, subjects: SubjectBucketList, patch_handler):
        self.subjects = subjects
        self.patch_handler = patch_handler
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
                    return outer.patch_handler(prompt)
                raise AssertionError(f"Unexpected requested schema: {schema.__name__}")

        return StructuredOutput()

    def patch_prompts_for(self, user_id: str) -> list[str]:
        return [
            prompt
            for schema, prompt in self.calls
            if schema is PatchProposalList and f"Obj_id = {user_id}" in prompt
        ]


def compile_checkpointed_parent():
    return graphv3.parent_builder.compile(checkpointer=InMemorySaver())


def build_parent_state() -> MainState:
    return MainState(
        messages=[
            HumanMessage(id="hm_john", content="John moved to Miami."),
            HumanMessage(
                id="hm_philip",
                content="Philip is interested in AI hiring.",
            ),
        ],
        existing={
            "user_john": UserProfile(name="John", location="London"),
            "user_philip": UserProfile(
                name="Philip",
                role="Owner",
                location="London",
                interests=["metals"],
            ),
        },
    )


def update_subjects() -> SubjectBucketList:
    return SubjectBucketList(
        items=[
            existing_subject("John", "hm_john", "user_john"),
            existing_subject("Philip", "hm_philip", "user_philip"),
        ]
    )


def test_parallel_successful_and_model_repaired_updates_both_commit(monkeypatch):
    def patches(prompt):
        if "Obj_id = user_john:" in prompt:
            assert "FAILED RAW CANDIDATE:" not in prompt
            return replace_field("user_john", "/location", "Miami")
        if "FAILED RAW CANDIDATE:" in prompt:
            assert "VALIDATION ERRORS:" in prompt
            return replace_field(
                "user_philip",
                "/interests",
                ["metals", "AI hiring"],
            )
        return replace_field("user_philip", "/interests", "AI hiring")

    fake_llm = ParallelRepairLLM(update_subjects(), patches)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()

    result = graph.invoke(
        build_parent_state(),
        config={"configurable": {"thread_id": "parallel-model-repair"}},
    )

    assert result["existing"] == {
        "user_john": UserProfile(name="John", location="Miami"),
        "user_philip": UserProfile(
            name="Philip",
            role="Owner",
            location="London",
            interests=["metals", "AI hiring"],
        ),
    }
    assert len(fake_llm.patch_prompts_for("user_john")) == 1
    philip_prompts = fake_llm.patch_prompts_for("user_philip")
    assert len(philip_prompts) == 2
    assert "FAILED RAW CANDIDATE:" not in philip_prompts[0]
    assert "FAILED RAW CANDIDATE:" in philip_prompts[1]


def test_human_repair_preserves_completed_sibling_and_resume_merges_repair(
    monkeypatch,
):
    def patches(prompt):
        if "Obj_id = user_john:" in prompt:
            return replace_field("user_john", "/location", "Miami")
        return replace_field("user_philip", "/interests", "AI hiring")

    fake_llm = ParallelRepairLLM(update_subjects(), patches)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = {"configurable": {"thread_id": "parallel-human-repair"}}
    original_state = build_parent_state()

    interrupted_result = graph.invoke(original_state, config=config)
    snapshot = graph.get_state(config)

    assert "__interrupt__" in interrupted_result
    assert len(snapshot.interrupts) == 1
    pending_interrupt = snapshot.interrupts[0]
    assert pending_interrupt.value["target_id"] == "user_philip"
    assert snapshot.values["existing"]["user_john"].location == "Miami"
    assert (
        snapshot.values["existing"]["user_philip"]
        == original_state.existing["user_philip"]
    )
    john_calls_before_resume = len(fake_llm.patch_prompts_for("user_john"))

    resume_payload = {
        "items": [
            {
                "target_id": "user_philip",
                "patches": [
                    {
                        "op": "replace",
                        "path": "/interests",
                        "value": ["metals", "AI hiring"],
                    }
                ],
            }
        ]
    }
    result = graph.invoke(
        Command(resume={pending_interrupt.id: resume_payload}),
        config=config,
    )
    completed_snapshot = graph.get_state(config)

    assert completed_snapshot.interrupts == ()
    assert result["existing"] == {
        "user_john": UserProfile(name="John", location="Miami"),
        "user_philip": UserProfile(
            name="Philip",
            role="Owner",
            location="London",
            interests=["metals", "AI hiring"],
        ),
    }
    assert len(fake_llm.patch_prompts_for("user_john")) == john_calls_before_resume


def test_multiple_human_repairs_resume_one_at_a_time_by_interrupt_id(monkeypatch):
    profiles = {
        "user_john": UserProfile(name="John", interests=["football"]),
        "user_philip": UserProfile(name="Philip", interests=["metals"]),
        "user_lucia": UserProfile(name="Lucia", interests=["law"]),
    }
    messages = [
        HumanMessage(id="hm_john", content="John likes cycling."),
        HumanMessage(id="hm_philip", content="Philip likes AI hiring."),
        HumanMessage(id="hm_lucia", content="Lucia likes gardening."),
    ]
    subjects = SubjectBucketList(
        items=[
            existing_subject("John", "hm_john", "user_john"),
            existing_subject("Philip", "hm_philip", "user_philip"),
            existing_subject("Lucia", "hm_lucia", "user_lucia"),
        ]
    )
    repaired_interests = {
        "user_john": ["football", "cycling"],
        "user_philip": ["metals", "AI hiring"],
        "user_lucia": ["law", "gardening"],
    }

    def patches(prompt):
        for user_id in profiles:
            if f"Obj_id = {user_id}" in prompt:
                return replace_field(user_id, "/interests", "invalid list")
        raise AssertionError("Patch prompt did not identify a known target")

    fake_llm = ParallelRepairLLM(subjects, patches)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = {"configurable": {"thread_id": "parallel-multiple-human-repair"}}

    interrupted_result = graph.invoke(
        MainState(messages=messages, existing=profiles),
        config=config,
    )
    snapshot = graph.get_state(config)

    assert "__interrupt__" in interrupted_result
    assert len(snapshot.interrupts) == 3
    interrupts_by_target = {
        pending.value["target_id"]: pending for pending in snapshot.interrupts
    }
    assert set(interrupts_by_target) == set(profiles)
    assert snapshot.values["existing"] == profiles
    calls_before_resume = {
        user_id: len(fake_llm.patch_prompts_for(user_id)) for user_id in profiles
    }

    result = interrupted_result
    unresolved_targets = set(profiles)
    for _ in profiles:
        pending = result["__interrupt__"][0]
        user_id = pending.value["target_id"]
        resume_payload = {
            "items": [
                {
                    "target_id": user_id,
                    "patches": [
                        {
                            "op": "replace",
                            "path": "/interests",
                            "value": repaired_interests[user_id],
                        }
                    ],
                }
            ]
        }
        result = graph.invoke(
            Command(resume={pending.id: resume_payload}),
            config=config,
        )
        unresolved_targets.remove(user_id)
        snapshot = graph.get_state(config)

        assert (
            snapshot.values["existing"][user_id].interests
            == repaired_interests[user_id]
        )
        assert {
            interrupt.value["target_id"]
            for interrupt in result.get("__interrupt__", ())
        } == unresolved_targets
        for unresolved_id in unresolved_targets:
            assert snapshot.values["existing"][unresolved_id] == profiles[unresolved_id]

    assert "__interrupt__" not in result
    assert result["existing"] == {
        user_id: profile.model_copy(
            update={"interests": repaired_interests[user_id]}
        )
        for user_id, profile in profiles.items()
    }
    assert {
        user_id: len(fake_llm.patch_prompts_for(user_id)) for user_id in profiles
    } == calls_before_resume
