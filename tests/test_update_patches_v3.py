from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import PatchOp, PatchProposal, PatchProposalList, UpdateAgentState, UserProfile


# This file tests only the update_patches() step.
#
# It does NOT test:
# - apply_patch()
# - Send fan-out
# - wrappers
# - downstream update-subgraph nodes
#
# It verifies that update_patches():
# - enforces the one-profile contract
# - calls the structured-output LLM path for a valid one-profile state
# - stores the returned PatchProposalList.items into patches
# - includes the target profile and supporting messages in the prompt


def build_valid_state() -> UpdateAgentState:
    return UpdateAgentState(
        messages=[
            HumanMessage(
                id="hm_001",
                content="Philip de Haas now lives in Zurich and is interested in AI hiring.",
            )
        ],
        existing={
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=["metals"],
            )
        },
    )


class FakeStructuredLLM:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return self.result


class FakeLLM:
    def __init__(self, result):
        self.result = result
        self.structured_calls = []
        self.fake_structured_llm = FakeStructuredLLM(result)

    def with_structured_output(self, schema):
        self.structured_calls.append(schema)
        return self.fake_structured_llm


def test_update_patches_happy_path():
    fake_result = PatchProposalList(
        items=[
            PatchProposal(
                target_id="user_001",
                patches=[
                    PatchOp(op="replace", path="/location", value="Zurich"),
                    PatchOp(op="add", path="/interests/-", value="AI hiring"),
                ],
            )
        ]
    )

    fake_llm = FakeLLM(fake_result)
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_valid_state()
        result = graphv3.update_patches(state)

        assert fake_llm.structured_calls == [PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 1
        sent_messages = fake_llm.fake_structured_llm.calls[0]
        assert len(sent_messages) == 1
        assert isinstance(sent_messages[0], SystemMessage)
        prompt = sent_messages[0].content
        assert "TARGET EXISTING PROFILE:" in prompt
        assert "RELEVANT MESSAGE(S) FOR THIS PROFILE:" in prompt
        assert "Philip de Haas" in prompt
        assert "Philip de Haas now lives in Zurich and is interested in AI hiring." in prompt
        assert "patches" in result
        assert result["patches"] == fake_result.items
    finally:
        graphv3.llm = original_llm


def test_update_patches_rejects_zero_targets():
    state = build_valid_state()
    state.existing = {}

    with pytest.raises(ValueError) as exc_info:
        graphv3.update_patches(state)
    assert "exactly one target profile" in str(exc_info.value)


def test_update_patches_rejects_multiple_targets():
    state = build_valid_state()
    state.existing["user_002"] = UserProfile(
        name="Mario Fishman",
        company="Krowdy",
        role="CEO",
        location="Peru",
        interests=[],
    )

    with pytest.raises(ValueError) as exc_info:
        graphv3.update_patches(state)
    assert "exactly one target profile" in str(exc_info.value)
