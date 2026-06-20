from pathlib import Path
import re
import sys
from threading import Lock

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import (
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


def existing_id_for_name(prompt: str, name: str) -> str:
    match = re.search(rf"Obj_id = ([^:]+):\nname : {re.escape(name)}\n", prompt)
    assert match is not None, f"Expected existing profile for {name!r} in planner prompt."
    return match.group(1)


def replace_fields(user_id: str, **fields: str) -> PatchProposalList:
    return PatchProposalList(
        items=[
            PatchProposal(
                target_id=user_id,
                patches=[
                    PatchOp(op="replace", path=f"/{field}", value=value)
                    for field, value in fields.items()
                ],
            )
        ]
    )


class ScenarioLLM:
    """Route deterministic outputs by schema and checkpoint-aware prompt content."""

    def __init__(self, subject_handler, profile_handler, patch_handler):
        self.subject_handler = subject_handler
        self.profile_handler = profile_handler
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
                    return outer.subject_handler(prompt)
                if schema is UserProfile:
                    return outer.profile_handler(prompt)
                if schema is PatchProposalList:
                    return outer.patch_handler(prompt)
                raise AssertionError(f"Unexpected requested schema: {schema.__name__}")

        return StructuredOutput()

    def prompts_for(self, schema):
        return [prompt for called_schema, prompt in self.calls if called_schema is schema]


def compile_checkpointed_parent():
    return graphv3.parent_builder.compile(checkpointer=InMemorySaver())


def thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def message_ids(snapshot) -> list[str]:
    return [message.id for message in snapshot.values["messages"]]


def assert_no_extract_local_state_leaks(snapshot) -> None:
    assert "candidate" not in snapshot.values
    assert "errors" not in snapshot.values


def test_sparse_create_enrichment_and_correction_reuse_one_profile(monkeypatch):
    def subjects(prompt):
        if "id: hm_003" in prompt:
            return SubjectBucketList(
                items=[
                    existing_subject(
                        "Lucia",
                        ["hm_003"],
                        existing_id_for_name(prompt, "Lucia"),
                    )
                ]
            )
        if "id: hm_002" in prompt:
            return SubjectBucketList(
                items=[
                    existing_subject(
                        "Lucia",
                        ["hm_002"],
                        existing_id_for_name(prompt, "Lucia"),
                    )
                ]
            )
        return SubjectBucketList(items=[new_subject("Lucia", ["hm_001"])])

    def profile(prompt):
        assert "new subject labeled:\nLucia" in prompt
        return UserProfile(name="Lucia")

    def patches(prompt):
        user_id = existing_id_for_name(prompt, "Lucia")
        if "Lucia moved to Cusco." in prompt:
            return replace_fields(user_id, location="Cusco")
        assert "Lucia is a lawyer from Lima." in prompt
        return replace_fields(user_id, role="Lawyer", location="Lima")

    fake_llm = ScenarioLLM(subjects, profile, patches)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = thread_config("sparse-enrichment-correction")

    first = graph.invoke(
        {"messages": [HumanMessage(id="hm_001", content="I met Lucia.")]},
        config=config,
    )
    created_id = next(iter(first["existing"]))
    assert first["existing"] == {created_id: UserProfile(name="Lucia")}
    assert len(fake_llm.prompts_for(UserProfile)) == 1
    assert_no_extract_local_state_leaks(graph.get_state(config))

    second = graph.invoke(
        {
            "messages": [
                HumanMessage(id="hm_002", content="Lucia is a lawyer from Lima.")
            ]
        },
        config=config,
    )
    assert second["existing"] == {
        created_id: UserProfile(name="Lucia", role="Lawyer", location="Lima")
    }
    assert len(fake_llm.prompts_for(UserProfile)) == 1

    third = graph.invoke(
        {"messages": [HumanMessage(id="hm_003", content="Lucia moved to Cusco.")]},
        config=config,
    )
    assert third["existing"] == {
        created_id: UserProfile(name="Lucia", role="Lawyer", location="Cusco")
    }
    snapshot = graph.get_state(config)
    assert message_ids(snapshot) == ["hm_001", "hm_002", "hm_003"]
    assert_no_extract_local_state_leaks(snapshot)


def test_several_created_profiles_then_one_selected_update(monkeypatch):
    def subjects(prompt):
        if "id: hm_003" in prompt:
            return SubjectBucketList(
                items=[
                    existing_subject(
                        "Lucia",
                        ["hm_003"],
                        existing_id_for_name(prompt, "Lucia"),
                    )
                ]
            )
        return SubjectBucketList(
            items=[
                new_subject("Lucia", ["hm_001"]),
                new_subject("Maria", ["hm_002"]),
            ]
        )

    def profile(prompt):
        if "new subject labeled:\nLucia" in prompt:
            return UserProfile(name="Lucia", role="Lawyer")
        assert "new subject labeled:\nMaria" in prompt
        return UserProfile(name="Maria", role="Engineer")

    def patches(prompt):
        user_id = existing_id_for_name(prompt, "Lucia")
        return replace_fields(user_id, location="Lima")

    fake_llm = ScenarioLLM(subjects, profile, patches)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = thread_config("several-then-selected-update")

    first = graph.invoke(
        {
            "messages": [
                HumanMessage(id="hm_001", content="I met Lucia, a lawyer."),
                HumanMessage(id="hm_002", content="I met Maria, an engineer."),
            ]
        },
        config=config,
    )
    ids_by_name = {
        profile.name: user_id for user_id, profile in first["existing"].items()
    }
    assert len(fake_llm.prompts_for(UserProfile)) == 2
    assert_no_extract_local_state_leaks(graph.get_state(config))

    second = graph.invoke(
        {"messages": [HumanMessage(id="hm_003", content="Lucia lives in Lima.")]},
        config=config,
    )

    assert set(second["existing"]) == set(ids_by_name.values())
    assert second["existing"][ids_by_name["Lucia"]] == UserProfile(
        name="Lucia",
        role="Lawyer",
        location="Lima",
    )
    assert second["existing"][ids_by_name["Maria"]] == UserProfile(
        name="Maria",
        role="Engineer",
    )
    assert len(fake_llm.prompts_for(UserProfile)) == 2
    assert_no_extract_local_state_leaks(graph.get_state(config))


def test_no_subject_later_turn_clears_buckets_but_preserves_state(monkeypatch):
    def subjects(prompt):
        if "id: hm_002" in prompt:
            return SubjectBucketList()
        return SubjectBucketList(items=[new_subject("Lucia", ["hm_001"])])

    def profile(prompt):
        assert "new subject labeled:\nLucia" in prompt
        return UserProfile(name="Lucia")

    def unexpected_patches(prompt):
        raise AssertionError("No update branch should run in this scenario.")

    fake_llm = ScenarioLLM(subjects, profile, unexpected_patches)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = thread_config("no-subject-clears-buckets")

    first = graph.invoke(
        {"messages": [HumanMessage(id="hm_001", content="I met Lucia.")]},
        config=config,
    )
    existing = first["existing"]
    calls_before_second_turn = len(fake_llm.calls)
    assert len(fake_llm.prompts_for(UserProfile)) == 1
    assert_no_extract_local_state_leaks(graph.get_state(config))

    second = graph.invoke(
        {"messages": [HumanMessage(id="hm_002", content="It rained yesterday.")]},
        config=config,
    )
    snapshot = graph.get_state(config)

    assert second["existing"] == existing
    assert snapshot.values["subjects"] == SubjectBucketList()
    assert message_ids(snapshot) == ["hm_001", "hm_002"]
    assert [schema for schema, _ in fake_llm.calls[calls_before_second_turn:]] == [
        SubjectBucketList
    ]
    assert len(fake_llm.prompts_for(UserProfile)) == 1
    assert_no_extract_local_state_leaks(snapshot)


def test_same_thread_accumulates_while_different_threads_stay_isolated(monkeypatch):
    def subjects(prompt):
        if "id: hm_a2" in prompt:
            return SubjectBucketList(
                items=[
                    existing_subject(
                        "Lucia",
                        ["hm_a2"],
                        existing_id_for_name(prompt, "Lucia"),
                    )
                ]
            )
        if "id: hm_a1" in prompt:
            return SubjectBucketList(items=[new_subject("Lucia", ["hm_a1"])])
        assert "id: hm_b1" in prompt
        assert "hm_a1" not in prompt
        assert "hm_a2" not in prompt
        assert "name : Lucia" not in prompt
        return SubjectBucketList(items=[new_subject("Maria", ["hm_b1"])])

    def profile(prompt):
        if "new subject labeled:\nLucia" in prompt:
            return UserProfile(name="Lucia")
        assert "new subject labeled:\nMaria" in prompt
        return UserProfile(name="Maria")

    def patches(prompt):
        user_id = existing_id_for_name(prompt, "Lucia")
        return replace_fields(user_id, role="Lawyer")

    fake_llm = ScenarioLLM(subjects, profile, patches)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config_a = thread_config("isolated-thread-a")
    config_b = thread_config("isolated-thread-b")

    graph.invoke(
        {"messages": [HumanMessage(id="hm_a1", content="I met Lucia.")]},
        config=config_a,
    )
    graph.invoke(
        {"messages": [HumanMessage(id="hm_a2", content="Lucia is a lawyer.")]},
        config=config_a,
    )
    graph.invoke(
        {"messages": [HumanMessage(id="hm_b1", content="I met Maria.")]},
        config=config_b,
    )

    snapshot_a = graph.get_state(config_a)
    snapshot_b = graph.get_state(config_b)
    assert_no_extract_local_state_leaks(snapshot_a)
    assert_no_extract_local_state_leaks(snapshot_b)
    assert len(fake_llm.prompts_for(UserProfile)) == 2
    assert message_ids(snapshot_a) == ["hm_a1", "hm_a2"]
    assert message_ids(snapshot_b) == ["hm_b1"]
    assert [profile.name for profile in snapshot_a.values["existing"].values()] == [
        "Lucia"
    ]
    assert [profile.name for profile in snapshot_b.values["existing"].values()] == [
        "Maria"
    ]
    assert snapshot_a.values["subjects"].items[0].classification == "existing"
    assert snapshot_b.values["subjects"].items[0].classification == "new"
