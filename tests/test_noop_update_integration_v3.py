from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
from langgraph.types import Send

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import MainState, MessageSelectionOutput, PatchProposalList, UpdateLink, UserProfile, merge_profiles


def build_state() -> MainState:
    return MainState(
        messages=[
            HumanMessage(
                id="hm_001",
                content="Mario likes tae kwon do.",
            )
        ],
        existing={
            "user_001": UserProfile(
                name="Mario",
                company=None,
                role=None,
                location=None,
                interests=["tae kwon do"],
            )
        },
        plan=MessageSelectionOutput(
            reasoning_summary_for_create="",
            reasoning_summary_for_update=(
                "Mario is mentioned again, but there may be no actual profile field change."
            ),
            relevant_for_create_links=[],
            relevant_for_update_links=[
                UpdateLink(message_id="hm_001", user_profile_ids=["user_001"]),
            ],
        ),
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


def test_parent_update_path_allows_noop_patch_result_without_crashing():
    fake_llm = FakeLLM([PatchProposalList(items=[])])
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_state()
        original_profile = state.existing["user_001"].model_dump()

        destinations = graphv3.route_after_planner(state)

        sends = [item for item in destinations if isinstance(item, Send)]
        assert len(sends) == 1
        assert destinations == sends
        assert sends[0].node == "update_subagent"
        assert list(sends[0].arg["existing"].keys()) == ["user_001"]
        assert [msg.id for msg in sends[0].arg["messages"]] == ["hm_001"]

        per_user_state = MainState(**sends[0].arg)
        result = graphv3.run_update_subgagent(per_user_state)

        assert fake_llm.structured_calls == [PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 1
        assert result["existing"]["user_001"].name == "Mario"

        assert set(result["existing"].keys()) == {"user_001"}
        committed_profile = result["existing"]["user_001"]
        assert committed_profile.model_dump() == original_profile

        merged_existing = merge_profiles(state.existing, result["existing"])
        assert set(merged_existing.keys()) == {"user_001"}
        assert merged_existing["user_001"].model_dump() == original_profile
    finally:
        graphv3.llm = original_llm
