from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import MainState, PatchProposalList, SubjectBucket, SubjectBucketList, UserProfile


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


class CapturingSubgraph:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def invoke(self, state):
        self.calls.append(state)
        return self.result


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


def routed_update_payload(
    profile: UserProfile,
    messages: list[HumanMessage],
) -> dict:
    subject = existing_subject(
        profile.name or "selected profile",
        [message.id for message in messages],
        "user_001",
    )
    state = MainState(
        messages=messages,
        existing={"user_001": profile},
        subjects=SubjectBucketList(items=[subject]),
    )
    return graphv3.fan_out_updates(state)[0].arg


def test_update_wrapper_preserves_real_routed_payload_and_returns_partial_update(
    monkeypatch,
):
    profile = UserProfile(name="John", location="London")
    messages = [
        HumanMessage(id="hm_001", content="John moved to Miami."),
        HumanMessage(id="hm_002", content="John became a director."),
    ]
    payload = routed_update_payload(profile, messages)
    committed_profile = UserProfile(name="John", role="Director", location="Miami")
    existing_slice = {"user_001": committed_profile}
    fake_subgraph = CapturingSubgraph(
        {"existing": existing_slice, "candidate": {"ignored": "value"}}
    )
    monkeypatch.setattr(graphv3, "update_subgraph", fake_subgraph)

    result = graphv3.run_update_subgagent(payload)

    assert len(fake_subgraph.calls) == 1
    sub_state = fake_subgraph.calls[0]
    assert set(sub_state) == {"messages", "existing"}
    assert sub_state["existing"] == {"user_001": profile}
    assert [message.id for message in sub_state["messages"]] == ["hm_001", "hm_002"]
    assert result == {"existing": existing_slice}


def test_routed_noop_update_completes_through_real_update_subgraph(monkeypatch):
    profile = UserProfile(
        name="John",
        company="Example Co",
        role="Director",
        location="London",
        interests=["football"],
    )
    payload = routed_update_payload(
        profile,
        [HumanMessage(id="hm_001", content="I spoke with John yesterday.")],
    )
    fake_llm = FakeLLM(PatchProposalList())
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    result = graphv3.run_update_subgagent(payload)

    assert fake_llm.structured_calls == [PatchProposalList]
    assert len(fake_llm.fake_structured_llm.calls) == 1
    assert result == {"existing": {"user_001": profile}}


def test_declined_update_branch_returns_unchanged_profile_slice(monkeypatch):
    profile = UserProfile(name="John", location="London")
    payload = routed_update_payload(
        profile,
        [HumanMessage(id="hm_001", content="John moved to Miami.")],
    )
    unchanged_slice = {"user_001": profile}
    fake_subgraph = CapturingSubgraph({"existing": unchanged_slice})
    monkeypatch.setattr(graphv3, "update_subgraph", fake_subgraph)

    result = graphv3.run_update_subgagent(payload)

    assert fake_subgraph.calls == [
        {
            "messages": payload["messages"],
            "existing": {"user_001": profile},
        }
    ]
    assert result == {"existing": unchanged_slice}


@pytest.mark.parametrize(
    ("payload", "missing_key"),
    [
        ({"messages": []}, "existing"),
        ({"existing": {"user_001": UserProfile(name="John")}}, "messages"),
    ],
)
def test_update_wrapper_missing_required_routed_state_fails_before_invoke(
    monkeypatch,
    payload,
    missing_key,
):
    fake_subgraph = CapturingSubgraph({"existing": {}})
    monkeypatch.setattr(graphv3, "update_subgraph", fake_subgraph)

    with pytest.raises(KeyError, match=missing_key):
        graphv3.run_update_subgagent(payload)

    assert fake_subgraph.calls == []
