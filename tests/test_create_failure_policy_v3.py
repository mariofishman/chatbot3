from pathlib import Path
import sys
from threading import Lock
from uuid import UUID

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
import pytest

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


class CreateFailureLLM:
    """Return deterministic parent outputs by schema and prompt content."""

    def __init__(
        self,
        subjects: SubjectBucketList,
        profiles_by_label: dict[str, list[object]] | None = None,
        patches_by_id: dict[str, PatchProposalList] | None = None,
    ):
        self.subjects = subjects
        self.profiles_by_label = {
            label: list(results)
            for label, results in (profiles_by_label or {}).items()
        }
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
                    for label, results in outer.profiles_by_label.items():
                        if f"new subject labeled:\n{label}" in prompt:
                            if not results:
                                raise AssertionError(
                                    f"No fake UserProfile result left for {label}."
                                )
                            result = results.pop(0)
                            if isinstance(result, BaseException):
                                raise result
                            return result
                if schema is PatchProposalList:
                    for user_id, patches in outer.patches_by_id.items():
                        if f"Obj_id = {user_id}:" in prompt:
                            return patches
                raise AssertionError(
                    f"No fake output configured for schema={schema.__name__}."
                )

        return StructuredOutput()

    def prompts_for(self, schema) -> list[str]:
        return [prompt for called_schema, prompt in self.calls if called_schema is schema]


def compile_checkpointed_parent():
    return graphv3.parent_builder.compile(checkpointer=InMemorySaver())


def one_new_lucia_state() -> MainState:
    return MainState(
        messages=[
            HumanMessage(id="hm_lucia", content="Lucia is a lawyer from Lima.")
        ]
    )


def profile_names(existing: dict[str, UserProfile]) -> set[str | None]:
    return {profile.name for profile in existing.values()}


def only_profile(existing: dict[str, UserProfile]) -> UserProfile:
    assert len(existing) == 1
    created_id, profile = next(iter(existing.items()))
    UUID(created_id)
    return profile


def interrupted_single_create(monkeypatch, thread_id: str):
    subjects = SubjectBucketList(items=[new_subject("Lucia", ["hm_lucia"])])
    fake_llm = CreateFailureLLM(
        subjects,
        profiles_by_label={"Lucia": [None, UserProfile()]},
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(one_new_lucia_state(), config=config)

    assert "__interrupt__" in result
    assert len(result["__interrupt__"]) == 1
    return graph, config, result, fake_llm


def test_first_extraction_succeeds_without_retry_or_interrupt(monkeypatch):
    profile = UserProfile(name="Lucia", role="Lawyer", location="Lima")
    fake_llm = CreateFailureLLM(
        SubjectBucketList(items=[new_subject("Lucia", ["hm_lucia"])]),
        profiles_by_label={"Lucia": [profile]},
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = compile_checkpointed_parent().invoke(
        one_new_lucia_state(),
        config={"configurable": {"thread_id": "create-success"}},
    )

    assert "__interrupt__" not in result
    assert only_profile(result["existing"]) == profile
    assert len(fake_llm.prompts_for(UserProfile)) == 1


def test_first_extraction_failure_retries_and_commits(monkeypatch):
    profile = UserProfile(name="Lucia", role="Lawyer")
    fake_llm = CreateFailureLLM(
        SubjectBucketList(items=[new_subject("Lucia", ["hm_lucia"])]),
        profiles_by_label={
            "Lucia": [OutputParserException("malformed output"), profile]
        },
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = compile_checkpointed_parent().invoke(
        one_new_lucia_state(),
        config={"configurable": {"thread_id": "create-retry-success"}},
    )

    assert "__interrupt__" not in result
    assert only_profile(result["existing"]) == profile
    prompts = fake_llm.prompts_for(UserProfile)
    assert len(prompts) == 2
    assert "EXTRACTION ERROR" in prompts[1]
    assert "malformed output" in prompts[1]
    assert "ORIGINAL TASK" in prompts[1]
    assert "Lucia is a lawyer from Lima." in prompts[1]


def test_two_extraction_failures_interrupt_without_exposing_candidate(monkeypatch):
    graph, config, result, fake_llm = interrupted_single_create(
        monkeypatch,
        "create-interrupt",
    )
    snapshot = graph.get_state(config)
    interrupt_payload = result["__interrupt__"][0].value

    assert len(fake_llm.prompts_for(UserProfile)) == 2
    assert snapshot.values["existing"] == {}
    assert "candidate" not in snapshot.values
    assert interrupt_payload["subject_label"] == "Lucia"
    assert "Lucia is a lawyer from Lima." in interrupt_payload["supporting_messages"]
    assert interrupt_payload["errors"]
    assert interrupt_payload["response_examples"] == [
        {"action": "submit", "profile": UserProfile.model_json_schema()},
        {"action": "decline"},
    ]


def test_valid_human_submit_commits_create_branch(monkeypatch):
    graph, config, result, fake_llm = interrupted_single_create(
        monkeypatch,
        "create-human-submit",
    )
    pending = result["__interrupt__"][0]
    submitted_profile = UserProfile(name="Lucia", role="Lawyer", location="Lima")

    result = graph.invoke(
        Command(
            resume={
                pending.id: {
                    "action": "submit",
                    "profile": submitted_profile.model_dump(),
                }
            }
        ),
        config=config,
    )

    assert "__interrupt__" not in result
    assert graph.get_state(config).interrupts == ()
    assert only_profile(result["existing"]) == submitted_profile
    assert len(fake_llm.prompts_for(UserProfile)) == 2


@pytest.mark.parametrize(
    "human_payload",
    [
        {"action": "decline"},
        {},
        {"action": "ignore"},
        "not a dict",
        {"action": "submit"},
        {"action": "submit", "profile": {}},
        {"action": "submit", "profile": {"unknown": "value"}},
    ],
)
def test_invalid_or_declined_human_response_ends_without_creating(
    monkeypatch,
    human_payload,
):
    graph, config, result, _ = interrupted_single_create(
        monkeypatch,
        f"create-human-invalid-{repr(human_payload)}",
    )
    pending = result["__interrupt__"][0]

    result = graph.invoke(
        Command(resume={pending.id: human_payload}),
        config=config,
    )
    snapshot = graph.get_state(config)

    assert "__interrupt__" not in result
    assert snapshot.interrupts == ()
    assert snapshot.values["existing"] == {}
    assert profile_names(result["existing"]) == set()


def test_successful_siblings_are_preserved_while_create_branch_is_interrupted(
    monkeypatch,
):
    john = UserProfile(name="John", location="London")
    lucia = UserProfile(name="Lucia", role="Lawyer")
    maria = UserProfile(name="Maria", role="Engineer")
    messages = [
        HumanMessage(id="hm_john", content="John moved to Miami."),
        HumanMessage(id="hm_lucia", content="Lucia is a lawyer."),
        HumanMessage(id="hm_maria", content="Maria is an engineer."),
    ]
    subjects = SubjectBucketList(
        items=[
            existing_subject("John", ["hm_john"], "user_john"),
            new_subject("Lucia", ["hm_lucia"]),
            new_subject("Maria", ["hm_maria"]),
        ]
    )
    fake_llm = CreateFailureLLM(
        subjects,
        profiles_by_label={"Lucia": [lucia], "Maria": [None, UserProfile()]},
        patches_by_id={"user_john": replace_field("user_john", "/location", "Miami")},
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = {"configurable": {"thread_id": "create-sibling-preservation"}}

    result = graph.invoke(
        MainState(messages=messages, existing={"user_john": john}),
        config=config,
    )
    snapshot = graph.get_state(config)

    assert "__interrupt__" in result
    assert len(snapshot.interrupts) == 1
    assert snapshot.interrupts[0].value["subject_label"] == "Maria"
    assert snapshot.values["existing"]["user_john"].location == "Miami"
    assert profile_names(snapshot.values["existing"]) == {"John", "Lucia"}

    result = graph.invoke(
        Command(
            resume={
                snapshot.interrupts[0].id: {
                    "action": "submit",
                    "profile": maria.model_dump(),
                }
            }
        ),
        config=config,
    )

    assert "__interrupt__" not in result
    assert profile_names(result["existing"]) == {"John", "Lucia", "Maria"}
    assert result["existing"]["user_john"].location == "Miami"


def test_several_create_interrupts_resume_one_at_a_time(monkeypatch):
    messages = [
        HumanMessage(id="hm_lucia", content="Lucia is a lawyer."),
        HumanMessage(id="hm_maria", content="Maria is an engineer."),
        HumanMessage(id="hm_ana", content="Ana is a designer."),
    ]
    subjects = SubjectBucketList(
        items=[
            new_subject("Lucia", ["hm_lucia"]),
            new_subject("Maria", ["hm_maria"]),
            new_subject("Ana", ["hm_ana"]),
        ]
    )
    profiles = {
        "Lucia": UserProfile(name="Lucia", role="Lawyer"),
        "Maria": UserProfile(name="Maria", role="Engineer"),
        "Ana": UserProfile(name="Ana", role="Designer"),
    }
    fake_llm = CreateFailureLLM(
        subjects,
        profiles_by_label={
            label: [None, UserProfile()] for label in profiles
        },
    )
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = compile_checkpointed_parent()
    config = {"configurable": {"thread_id": "several-create-interrupts"}}

    result = graph.invoke(MainState(messages=messages), config=config)

    assert "__interrupt__" in result
    assert len(graph.get_state(config).interrupts) == 3

    submitted_labels = {"Lucia", "Ana"}
    while result.get("__interrupt__"):
        pending = result["__interrupt__"][0]
        label = pending.value["subject_label"]
        payload = (
            {"action": "submit", "profile": profiles[label].model_dump()}
            if label in submitted_labels
            else {"action": "decline"}
        )

        result = graph.invoke(
            Command(resume={pending.id: payload}),
            config=config,
        )
        snapshot = graph.get_state(config)

        committed_names = profile_names(snapshot.values["existing"])
        assert "Maria" not in committed_names
        assert committed_names <= submitted_labels
        assert {
            interrupt.value["subject_label"]
            for interrupt in result.get("__interrupt__", ())
        }.isdisjoint(committed_names)

    assert graph.get_state(config).interrupts == ()
    assert profile_names(result["existing"]) == submitted_labels
