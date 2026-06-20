from pathlib import Path
import sys
from uuid import UUID

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import ExtractAgentState, MainState, SubjectBucket, SubjectBucketList, UserProfile


def new_subject(label: str, message_ids: list[str]) -> SubjectBucket:
    return SubjectBucket(
        subject_label=label,
        message_ids=message_ids,
        classification="new",
    )


class FakeStructuredLLM:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        if not self.results:
            raise AssertionError("FakeStructuredLLM ran out of scripted results.")
        result = self.results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


class FakeLLM:
    def __init__(self, *results):
        self.structured_calls = []
        self.fake_structured_llm = FakeStructuredLLM(results)

    def with_structured_output(self, schema):
        self.structured_calls.append(schema)
        return self.fake_structured_llm


class CapturingSubgraph:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def invoke(self, state):
        self.calls.append(state)
        return self.result


def only_created_profile(result) -> tuple[str, UserProfile]:
    assert len(result["existing"]) == 1
    return next(iter(result["existing"].items()))


def only_candidate_profile(result) -> UserProfile:
    assert result["errors"] == []
    assert "existing" not in result
    assert isinstance(result["candidate"], UserProfile)
    return result["candidate"]


def checkpointed_extract_graph():
    return graphv3.extract_builder.compile(checkpointer=InMemorySaver())


def interrupted_extract_state(monkeypatch, thread_id: str):
    fake_llm = FakeLLM(None, UserProfile())
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    graph = checkpointed_extract_graph()
    config = {"configurable": {"thread_id": thread_id}}
    state = ExtractAgentState(
        subject=new_subject("Lucia", ["hm_001"]),
        messages=[HumanMessage(id="hm_001", content="I met Lucia.")],
    )

    result = graph.invoke(state, config=config)

    assert "__interrupt__" in result
    assert len(result["__interrupt__"]) == 1
    return graph, config, result, fake_llm


def test_compiled_extract_subgraph_creates_one_named_profile(monkeypatch):
    profile = UserProfile(
        name="Lucia Romero",
        role="Lawyer",
        location="Lima",
        interests=["football"],
    )
    fake_llm = FakeLLM(profile)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    state = ExtractAgentState(
        subject=new_subject("Lucia Romero", ["hm_001"]),
        messages=[
            HumanMessage(
                id="hm_001",
                content="Lucia Romero is a lawyer from Lima who likes football.",
            )
        ],
    )

    result = graphv3.extract_subgraph.invoke(state)

    created_id, created_profile = only_created_profile(result)
    UUID(created_id)
    assert created_profile == profile
    assert fake_llm.structured_calls == [UserProfile]
    assert len(fake_llm.fake_structured_llm.calls) == 1


def test_compiled_extract_subgraph_accepts_sparse_valid_profile(monkeypatch):
    sparse_profile = UserProfile(role="Engineer")
    monkeypatch.setattr(graphv3, "llm", FakeLLM(sparse_profile))
    state = ExtractAgentState(
        subject=new_subject("unnamed engineer", ["hm_001"]),
        messages=[
            HumanMessage(id="hm_001", content="I met an engineer yesterday.")
        ],
    )

    result = graphv3.extract_subgraph.invoke(state)

    _, created_profile = only_created_profile(result)
    assert created_profile == sparse_profile
    assert created_profile.name is None
    assert created_profile.company is None
    assert created_profile.location is None
    assert created_profile.interests == []


def test_unnamed_relationship_label_constrains_extraction(monkeypatch):
    sparse_profile = UserProfile(role="Lawyer")
    fake_llm = FakeLLM(sparse_profile)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    message = HumanMessage(
        id="hm_001",
        content="John introduced me to his friend, who is a lawyer.",
    )
    state = ExtractAgentState(
        subject=new_subject("John's friend", ["hm_001"]),
        messages=[message],
    )

    result = graphv3.extract_node(state)

    created_profile = only_candidate_profile(result)
    prompt = fake_llm.fake_structured_llm.calls[0][0]
    assert isinstance(prompt, SystemMessage)
    assert "John's friend" in prompt.content
    assert prompt.content.count(message.content) == 1
    assert created_profile.name is None


def test_extract_node_prompt_contains_each_supporting_message_once(monkeypatch):
    profile = UserProfile(name="Lucia")
    fake_llm = FakeLLM(profile)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    messages = [
        HumanMessage(id="hm_001", content="I met Lucia."),
        HumanMessage(id="hm_002", content="Lucia is a lawyer."),
    ]
    state = ExtractAgentState(
        subject=new_subject("Lucia", ["hm_001", "hm_002"]),
        messages=messages,
    )

    result = graphv3.extract_node(state)

    assert only_candidate_profile(result) == profile
    assert len(fake_llm.fake_structured_llm.calls) == 1
    prompt = fake_llm.fake_structured_llm.calls[0][0].content
    assert "Lucia" in prompt
    for message in messages:
        assert prompt.count(message.id) == 1
        assert prompt.count(message.content) == 1


@pytest.mark.parametrize(
    "first_failure",
    [
        None,
        UserProfile(),
        OutputParserException("bad structured output"),
    ],
)
def test_first_extraction_failure_retries_once_and_commits(
    monkeypatch,
    first_failure,
):
    profile = UserProfile(name="Lucia", role="Lawyer")
    fake_llm = FakeLLM(first_failure, profile)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    state = ExtractAgentState(
        subject=new_subject("Lucia", ["hm_001"]),
        messages=[HumanMessage(id="hm_001", content="Lucia is a lawyer.")],
    )

    result = graphv3.extract_subgraph.invoke(state)

    _, created_profile = only_created_profile(result)
    assert created_profile == profile
    assert "__interrupt__" not in result
    assert len(fake_llm.fake_structured_llm.calls) == 2
    retry_prompt = fake_llm.fake_structured_llm.calls[1][0]
    assert isinstance(retry_prompt, SystemMessage)
    assert "Your previous attempt to extract one UserProfile failed" in retry_prompt.content
    assert "ORIGINAL TASK" in retry_prompt.content
    assert "Lucia is a lawyer." in retry_prompt.content


def test_two_extraction_failures_produce_one_human_interrupt(monkeypatch):
    graph, config, result, fake_llm = interrupted_extract_state(
        monkeypatch,
        "extract-human-interrupt",
    )

    interrupt_payload = result["__interrupt__"][0].value
    checkpoint = graph.get_state(config)

    assert len(fake_llm.fake_structured_llm.calls) == 2
    assert interrupt_payload["subject_label"] == "Lucia"
    assert "I met Lucia." in interrupt_payload["supporting_messages"]
    assert interrupt_payload["errors"]
    assert interrupt_payload["response_instruction"]
    assert interrupt_payload["response_examples"] == [
        {"action": "submit", "profile": UserProfile.model_json_schema()},
        {"action": "decline"},
    ]
    assert checkpoint.values["candidate"] is None
    assert checkpoint.values["errors"]
    assert checkpoint.values["existing"] == {}


def test_valid_human_create_repair_response_commits_once(monkeypatch):
    graph, config, _, fake_llm = interrupted_extract_state(
        monkeypatch,
        "extract-human-submit",
    )
    submitted_profile = UserProfile(name="Lucia", role="Lawyer")

    result = graph.invoke(
        Command(
            resume={
                "action": "submit",
                "profile": submitted_profile.model_dump(),
            }
        ),
        config=config,
    )

    created_id, created_profile = only_created_profile(result)
    UUID(created_id)
    assert created_profile == submitted_profile
    assert "__interrupt__" not in result
    assert len(fake_llm.fake_structured_llm.calls) == 2


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
def test_invalid_or_declined_human_create_repair_ends_without_creating(
    monkeypatch,
    human_payload,
):
    graph, config, _, _ = interrupted_extract_state(
        monkeypatch,
        f"extract-human-invalid-{repr(human_payload)}",
    )
    interrupt_id = graph.get_state(config).interrupts[0].id

    result = graph.invoke(Command(resume={interrupt_id: human_payload}), config=config)
    checkpoint = graph.get_state(config)

    assert "__interrupt__" not in result
    assert checkpoint.values["candidate"] is None
    assert checkpoint.values["errors"]
    assert checkpoint.values["existing"] == {}


@pytest.mark.parametrize(
    "state",
    [
        ExtractAgentState(
            subject=new_subject("Lucia", ["hm_001"]),
            messages=[HumanMessage(id="hm_001", content="I met Lucia.")],
            candidate=None,
        ),
        ExtractAgentState(
            subject=new_subject("Lucia", ["hm_001"]),
            messages=[HumanMessage(id="hm_001", content="I met Lucia.")],
            candidate=UserProfile(name="Lucia"),
            errors=["still invalid"],
        ),
        ExtractAgentState(
            subject=new_subject("Lucia", ["hm_001"]),
            messages=[HumanMessage(id="hm_001", content="I met Lucia.")],
            candidate=UserProfile(name="Lucia"),
            existing={"existing-id": UserProfile(name="Already committed")},
        ),
    ],
)
def test_commit_created_profile_rejects_invalid_state(monkeypatch, state):
    def fail_uuid4():
        raise AssertionError("Invalid commit state must not generate a UUID.")

    monkeypatch.setattr(graphv3.uuid, "uuid4", fail_uuid4)

    with pytest.raises(ValueError):
        graphv3.commit_created_profile(state)


def test_unexpected_extract_errors_propagate_without_retry(monkeypatch):
    fake_llm = FakeLLM(RuntimeError("provider down"))
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    state = ExtractAgentState(
        subject=new_subject("Lucia", ["hm_001"]),
        messages=[HumanMessage(id="hm_001", content="I met Lucia.")],
    )

    with pytest.raises(RuntimeError, match="provider down"):
        graphv3.extract_node(state)

    assert len(fake_llm.fake_structured_llm.calls) == 1


def test_create_recovery_routers_reject_contradictory_state():
    base = {
        "subject": new_subject("Lucia", ["hm_001"]),
        "messages": [HumanMessage(id="hm_001", content="I met Lucia.")],
    }
    candidate = UserProfile(name="Lucia")

    assert (
        graphv3.route_extraction(
            ExtractAgentState(**base, candidate=candidate)
        )
        == "commit_created_profile"
    )
    assert (
        graphv3.route_extraction(
            ExtractAgentState(**base, candidate=None, errors=["failed"])
        )
        == "human_create_repair"
    )
    with pytest.raises(ValueError):
        graphv3.route_extraction(
            ExtractAgentState(**base, candidate=candidate, errors=["failed"])
        )
    with pytest.raises(ValueError):
        graphv3.route_extraction(
            ExtractAgentState(**base, candidate=None, errors=[])
        )

    assert (
        graphv3.route_after_human_create_repair(
            ExtractAgentState(**base, candidate=candidate)
        )
        == "commit_created_profile"
    )
    assert (
        graphv3.route_after_human_create_repair(
            ExtractAgentState(**base, candidate=None)
        )
        == "__end__"
    )
    with pytest.raises(ValueError):
        graphv3.route_after_human_create_repair(
            ExtractAgentState(**base, candidate=candidate, errors=["failed"])
        )


def test_extract_wrapper_uses_real_routed_payload_and_returns_partial_update(
    monkeypatch,
):
    subject = new_subject("Lucia", ["hm_001"])
    state = MainState(
        messages=[
            HumanMessage(id="hm_001", content="I met Lucia."),
            HumanMessage(id="hm_002", content="Unrelated message."),
        ],
        subjects=SubjectBucketList(items=[subject]),
    )
    routed_payload = graphv3.fan_out_creates(state)[0].arg
    existing_slice = {"generated-id": UserProfile(name="Lucia")}
    fake_subgraph = CapturingSubgraph({"existing": existing_slice, "ignored": "value"})
    monkeypatch.setattr(graphv3, "extract_subgraph", fake_subgraph)

    result = graphv3.run_extract_subgagent(routed_payload)

    assert len(fake_subgraph.calls) == 1
    sub_state = fake_subgraph.calls[0]
    assert set(sub_state) == {"subject", "messages"}
    assert sub_state["subject"] == subject
    assert [message.id for message in sub_state["messages"]] == ["hm_001"]
    assert result == {"existing": existing_slice}


@pytest.mark.parametrize(
    ("payload", "missing_key"),
    [
        ({"messages": []}, "subject"),
        ({"subject": new_subject("Lucia", ["hm_001"])}, "messages"),
    ],
)
def test_extract_wrapper_missing_required_routed_state_fails_before_invoke(
    monkeypatch,
    payload,
    missing_key,
):
    fake_subgraph = CapturingSubgraph({"existing": {}})
    monkeypatch.setattr(graphv3, "extract_subgraph", fake_subgraph)

    with pytest.raises(KeyError, match=missing_key):
        graphv3.run_extract_subgagent(payload)

    assert fake_subgraph.calls == []
