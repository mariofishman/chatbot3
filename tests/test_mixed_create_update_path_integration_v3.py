from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
from langgraph.types import Send

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import CreateLink, MainState, MessageSelectionOutput, PatchOp, PatchProposal, PatchProposalList, UpdateLink, UserProfile, UserProfileList, merge_profiles


def build_state() -> MainState:
    return MainState(
        messages=[
            HumanMessage(
                id="hm_001",
                content="I met Lucia Romero from Lima, and Philip de Haas now lives in Zurich.",
            ),
            HumanMessage(
                id="hm_002",
                content="Lucia Romero is a startup lawyer.",
            ),
            HumanMessage(
                id="hm_003",
                content="Philip de Haas also works often from Geneva.",
            ),
        ],
        existing={
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=[],
            )
        },
        plan=MessageSelectionOutput(
            reasoning_summary_for_create="Lucia Romero is a new person from Lima and is a startup lawyer.",
            reasoning_summary_for_update="Philip de Haas has location-related updates.",
            relevant_for_create_links=[
                CreateLink(message_id="hm_001", new_person_count=1),
                CreateLink(message_id="hm_002", new_person_count=1),
            ],
            relevant_for_update_links=[
                UpdateLink(message_id="hm_001", user_profile_ids=["user_001"]),
                UpdateLink(message_id="hm_003", user_profile_ids=["user_001"]),
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


def test_mixed_create_update_parent_path_accumulates_both_branches():
    fake_llm = FakeLLM(
        [
            UserProfileList(
                items=[
                    UserProfile(
                        name="Lucia Romero",
                        company=None,
                        role="Startup Lawyer",
                        location="Lima",
                        interests=[],
                    )
                ]
            ),
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
        ]
    )
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_state()
        destinations = graphv3.route_after_planner(state)

        assert "extract_subagent" in destinations
        sends = [item for item in destinations if isinstance(item, Send)]
        assert len(sends) == 1

        send_payload = sends[0].arg
        assert [msg.id for msg in send_payload["messages"]] == ["hm_001", "hm_003"]

        create_result = graphv3.run_extract_subgagent(state)
        update_result = graphv3.run_update_subgagent(MainState(**send_payload))

        merged_existing = merge_profiles(
            create_result["existing"],
            update_result["existing"],
        )

        assert fake_llm.structured_calls == [UserProfileList, PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 2

        create_call = fake_llm.fake_structured_llm.calls[0][0].content
        update_call = fake_llm.fake_structured_llm.calls[1][0].content

        assert "hm_001" in create_call
        assert "hm_002" in create_call
        assert "hm_003" not in create_call

        assert "hm_001" in update_call
        assert "hm_003" in update_call
        assert "hm_002" not in update_call

        assert len(merged_existing) == 2

        created_profile = next(
            profile for user_id, profile in merged_existing.items() if user_id != "user_001"
        )
        updated_profile = merged_existing["user_001"]

        assert created_profile.name == "Lucia Romero"
        assert created_profile.location == "Lima"
        assert created_profile.role == "Startup Lawyer"

        assert updated_profile.name == "Philip de Haas"
        assert updated_profile.location == "Geneva"
    finally:
        graphv3.llm = original_llm
