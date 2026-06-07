from pathlib import Path
import sys

from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import CreateLink, MainState, MessageSelectionOutput, UserProfile, UserProfileList


def build_state() -> MainState:
    return MainState(
        messages=[
            HumanMessage(
                id="hm_001",
                content="I met Lucia Romero, a startup lawyer from Lima.",
            ),
            HumanMessage(
                id="hm_002",
                content="Philip de Haas now lives in Zurich.",
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
            reasoning_summary_for_create="Lucia Romero is a new person.",
            reasoning_summary_for_update="",
            relevant_for_create_links=[
                CreateLink(message_id="hm_001", new_person_count=1),
            ],
            relevant_for_update_links=[],
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


def test_create_only_parent_path_routes_filters_and_returns_new_profile():
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
            )
        ]
    )
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_state()
        destinations = graphv3.route_after_planner(state)

        assert destinations == ["extract_subagent"]

        result = graphv3.run_extract_subgagent(state)

        assert fake_llm.structured_calls == [UserProfileList]
        assert len(fake_llm.fake_structured_llm.calls) == 1
        sent_messages = fake_llm.fake_structured_llm.calls[0]
        assert len(sent_messages) == 1
        assert isinstance(sent_messages[0], SystemMessage)
        prompt = sent_messages[0].content
        assert "hm_001" in prompt
        assert "Lucia Romero" in prompt
        assert "hm_002" not in prompt
        assert "Philip de Haas now lives in Zurich." not in prompt
        assert "Lucia Romero is a new person." in prompt
        assert "Philip de Haas has a location update." not in prompt

        assert "existing" in result
        assert len(result["existing"]) == 1
        created_profile = next(iter(result["existing"].values()))
        assert created_profile.name == "Lucia Romero"
        assert created_profile.location == "Lima"
        assert created_profile.role == "Startup Lawyer"
    finally:
        graphv3.llm = original_llm
