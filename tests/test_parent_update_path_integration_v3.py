from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
from langgraph.types import Send

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import MainState, MessageSelectionOutput, PatchOp, PatchProposal, PatchProposalList, UpdateLink, UserProfile, merge_profiles


def build_state() -> MainState:
    return MainState(
        messages=[
            HumanMessage(
                id="hm_001",
                content="Philip de Haas now lives in Zurich and Mario Fishman is focused on AI hiring.",
            ),
            HumanMessage(
                id="hm_002",
                content="Philip de Haas also works often from Geneva.",
            ),
        ],
        existing={
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=["metals"],
            ),
            "user_002": UserProfile(
                name="Mario Fishman",
                company="Krowdy",
                role="CEO",
                location="Peru",
                interests=[],
            ),
        },
        plan=MessageSelectionOutput(
            reasoning_summary_for_create="",
            reasoning_summary_for_update=(
                "Philip de Haas has location-related updates and Mario Fishman has an interest update."
            ),
            relevant_for_create_links=[],
            relevant_for_update_links=[
                UpdateLink(message_id="hm_001", user_profile_ids=["user_001", "user_002"]),
                UpdateLink(message_id="hm_002", user_profile_ids=["user_001"]),
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


def test_parent_update_path_fans_out_runs_subgraphs_and_merges_results():
    fake_results = [
        PatchProposalList(
            items=[
                PatchProposal(
                    target_id="user_001",
                    patches=[
                        PatchOp(op="replace", path="/location", value="Geneva"),
                    ],
                )
            ]
        ),
        PatchProposalList(
            items=[
                PatchProposal(
                    target_id="user_002",
                    patches=[
                        PatchOp(op="replace", path="/interests", value=["AI hiring"]),
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
        destinations = graphv3.route_after_planner(state)

        sends = [item for item in destinations if isinstance(item, Send)]
        assert len(sends) == 2
        assert destinations == sends

        send_by_user = {
            next(iter(send.arg["existing"].keys())): send.arg for send in sends
        }
        assert [msg.id for msg in send_by_user["user_001"]["messages"]] == ["hm_001", "hm_002"]
        assert [msg.id for msg in send_by_user["user_002"]["messages"]] == ["hm_001"]

        merged_existing = {}
        for send in sends:
            per_user_state = MainState(**send.arg)
            result = graphv3.run_update_subgagent(per_user_state)
            merged_existing = merge_profiles(merged_existing, result["existing"])

        assert fake_llm.structured_calls == [PatchProposalList, PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 2

        assert set(merged_existing.keys()) == {"user_001", "user_002"}
        assert merged_existing["user_001"].location == "Geneva"
        assert merged_existing["user_001"].interests == ["metals"]
        assert merged_existing["user_002"].location == "Peru"
        assert merged_existing["user_002"].interests == ["AI hiring"]
    finally:
        graphv3.llm = original_llm
