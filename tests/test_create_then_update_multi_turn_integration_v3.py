from pathlib import Path
import sys
from uuid import uuid4

from langchain_core.messages import HumanMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import CreateLink, MessageSelectionOutput, PatchOp, PatchProposal, PatchProposalList, UpdateLink, UserProfile, UserProfileList


class FakeStructuredLLM:
    def __init__(self, schema, parent):
        self.schema = schema
        self.parent = parent

    def invoke(self, messages):
        self.parent.calls.append((self.schema, messages))
        queue = self.parent.results_by_schema.setdefault(self.schema, [])
        if not queue:
            raise AssertionError(
                f"FakeStructuredLLM has no scripted result left for schema {self.schema.__name__}."
            )
        next_result = queue.pop(0)
        return next_result() if callable(next_result) else next_result


class FakeLLM:
    def __init__(self):
        self.calls = []
        self.results_by_schema = {}

    def queue_result(self, schema, result):
        self.results_by_schema.setdefault(schema, []).append(result)

    def with_structured_output(self, schema):
        return FakeStructuredLLM(schema, self)


def test_parent_graph_can_create_then_update_same_person_across_two_turns():
    fake_llm = FakeLLM()
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        fake_llm.queue_result(
            MessageSelectionOutput,
            MessageSelectionOutput(
                reasoning_summary_for_create="Lucia is a new person introduced in this message.",
                reasoning_summary_for_update="",
                relevant_for_create_links=[
                    CreateLink(message_id="hm_001", new_person_count=1),
                ],
                relevant_for_update_links=[],
            ),
        )
        fake_llm.queue_result(
            UserProfileList,
            UserProfileList(
                items=[
                    UserProfile(
                        name="Lucia",
                        company=None,
                        role="Lawyer",
                        location="Lima",
                        interests=[],
                    )
                ]
            ),
        )

        thread_config = {"configurable": {"thread_id": f"test-{uuid4().hex}"}}

        turn_1_result = graphv3.graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        id="hm_001",
                        content="I met Lucia, a lawyer from Lima.",
                    )
                ],
                "existing": {},
            },
            config=thread_config,
        )

        assert len(turn_1_result["existing"]) == 1
        assert len(turn_1_result["plan"].relevant_for_create_links) == 1
        assert turn_1_result["plan"].relevant_for_update_links == []
        created_user_id = next(iter(turn_1_result["existing"].keys()))
        created_profile = turn_1_result["existing"][created_user_id]
        assert created_profile.name == "Lucia"
        assert created_profile.role == "Lawyer"
        assert created_profile.location == "Lima"
        assert created_profile.company is None

        fake_llm.queue_result(
            MessageSelectionOutput,
            MessageSelectionOutput(
                reasoning_summary_for_create="",
                reasoning_summary_for_update="Lucia now has a company update.",
                relevant_for_create_links=[],
                relevant_for_update_links=[
                    UpdateLink(message_id="hm_002", user_profile_ids=[created_user_id]),
                ],
            ),
        )
        fake_llm.queue_result(
            PatchProposalList,
            PatchProposalList(
                items=[
                    PatchProposal(
                        target_id=created_user_id,
                        patches=[
                            PatchOp(op="replace", path="/company", value="LawFirm 33A"),
                        ],
                    )
                ]
            ),
        )

        turn_2_result = graphv3.graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        id="hm_002",
                        content="Lucia works at LawFirm 33A.",
                    )
                ]
            },
            config=thread_config,
        )

        assert len(turn_2_result["existing"]) == 1
        assert set(turn_2_result["existing"].keys()) == {created_user_id}
        assert turn_2_result["plan"].relevant_for_create_links == []
        assert len(turn_2_result["plan"].relevant_for_update_links) == 1

        updated_profile = turn_2_result["existing"][created_user_id]
        assert updated_profile.name == "Lucia"
        assert updated_profile.role == "Lawyer"
        assert updated_profile.location == "Lima"
        assert updated_profile.company == "LawFirm 33A"

        snapshot = graphv3.graph.get_state(thread_config)
        snapshot_existing = snapshot.values["existing"]
        snapshot_message_ids = [message.id for message in snapshot.values["messages"]]
        assert len(snapshot_existing) == 1
        assert set(snapshot_existing.keys()) == {created_user_id}
        assert snapshot_existing[created_user_id].company == "LawFirm 33A"
        assert snapshot_message_ids == ["hm_001", "hm_002"]

        call_schemas = [schema for schema, _ in fake_llm.calls]
        assert call_schemas == [
            MessageSelectionOutput,
            UserProfileList,
            MessageSelectionOutput,
            PatchProposalList,
        ]
    finally:
        graphv3.llm = original_llm
