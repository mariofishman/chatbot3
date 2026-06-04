from pathlib import Path
import sys

from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import PatchOp, PatchProposal, PatchProposalList, UpdateAgentState, UserProfile


def build_state() -> UpdateAgentState:
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
        reasoning_summary_for_update="Philip de Haas has update-side changes.",
        candidate={
            "user_001": {
                "name": "Philip de Haas",
                "company": "London Metals Limited",
                "role": "Owner",
                "location": "Zurich",
                "interests": "AI hiring",
            }
        },
        errors={
            "user_001": [
                "interests: Input should be a valid list",
            ]
        },
        attempts=1,
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
        self.structured_calls = []
        self.fake_structured_llm = FakeStructuredLLM(result)

    def with_structured_output(self, schema):
        self.structured_calls.append(schema)
        return self.fake_structured_llm


def test_patch_happy_path_returns_replacement_patches_and_increments_attempts():
    fake_result = PatchProposalList(
        items=[
            PatchProposal(
                target_id="user_001",
                patches=[
                    PatchOp(op="replace", path="/interests", value=["metals", "AI hiring"]),
                ],
            )
        ]
    )
    fake_llm = FakeLLM(fake_result)
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_state()
        result = graphv3.patch(state)

        assert fake_llm.structured_calls == [PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 1
        sent_messages = fake_llm.fake_structured_llm.calls[0]
        assert len(sent_messages) == 1
        assert isinstance(sent_messages[0], SystemMessage)

        prompt = sent_messages[0].content
        assert "FAILED RAW CANDIDATE:" in prompt
        assert "VALIDATION ERRORS:" in prompt
        assert "interests : AI hiring" in prompt
        assert "interests: Input should be a valid list" in prompt

        assert result["patches"] == fake_result.items
        assert result["attempts"] == 2
    finally:
        graphv3.llm = original_llm


def test_patch_rejects_empty_errors():
    state = build_state()
    state.errors = {}

    try:
        graphv3.patch(state)
    except ValueError as e:
        assert "non-empty state.errors" in str(e)
        return

    raise AssertionError("patch() should reject empty state.errors.")


def test_patch_rejects_mismatched_candidate_id():
    state = build_state()
    state.candidate = {
        "user_999": state.candidate["user_001"],
    }

    try:
        graphv3.patch(state)
    except ValueError as e:
        assert "candidate_id" in str(e)
        return

    raise AssertionError("patch() should reject mismatched candidate ids.")
