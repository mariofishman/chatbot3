from pathlib import Path
import sys
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
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
        return self.results.pop(0)


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

    _, created_profile = only_created_profile(result)
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

    graphv3.extract_node(state)

    assert len(fake_llm.fake_structured_llm.calls) == 1
    prompt = fake_llm.fake_structured_llm.calls[0][0].content
    assert "Lucia" in prompt
    for message in messages:
        assert prompt.count(message.id) == 1
        assert prompt.count(message.content) == 1


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
