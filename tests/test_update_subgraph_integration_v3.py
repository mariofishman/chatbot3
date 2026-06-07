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
                content="Philip de Haas is also interested in AI hiring.",
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
        reasoning_summary_for_update="Philip de Haas has an interest update.",
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
    def __init__(self, results):
        self.structured_calls = []
        self.fake_structured_llm = FakeStructuredLLM(results)

    def with_structured_output(self, schema):
        self.structured_calls.append(schema)
        return self.fake_structured_llm


def test_update_subgraph_retries_once_then_commits_successfully():
    fake_results = [
        PatchProposalList(
            items=[
                PatchProposal(
                    target_id="user_001",
                    patches=[
                        PatchOp(op="replace", path="/interests", value="AI hiring"),
                    ],
                )
            ]
        ),
        PatchProposalList(
            items=[
                PatchProposal(
                    target_id="user_001",
                    patches=[
                        PatchOp(
                            op="replace",
                            path="/interests",
                            value=["metals", "AI hiring"],
                        ),
                    ],
                )
            ]
        ),
    ]
    fake_llm = FakeLLM(fake_results)
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_state()
        result = graphv3.update_subgraph.invoke(state)

        assert fake_llm.structured_calls == [PatchProposalList, PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 2

        first_call = fake_llm.fake_structured_llm.calls[0]
        second_call = fake_llm.fake_structured_llm.calls[1]
        assert len(first_call) == 1
        assert len(second_call) == 1
        assert isinstance(first_call[0], SystemMessage)
        assert isinstance(second_call[0], SystemMessage)
        assert "TARGET EXISTING PROFILE:" in first_call[0].content
        assert "FAILED RAW CANDIDATE:" in second_call[0].content
        assert "VALIDATION ERRORS:" in second_call[0].content

        assert result["attempts"] == 1
        assert result["errors"] == {}
        assert "user_001" in result["existing"]
        updated_profile = result["existing"]["user_001"]
        assert isinstance(updated_profile, UserProfile)
        assert updated_profile.interests == ["metals", "AI hiring"]
        assert updated_profile.location == "London"
    finally:
        graphv3.llm = original_llm
