from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import CreateLink, ExtractAgentState, MainState, MessageSelectionOutput, UserProfile, UserProfileList


# This file tests only the create-side extract flow.
#
# It does NOT test:
# - human()
# - planner LLM behavior
# - update-side routing or wrappers
#
# It verifies:
# - run_extract_subgagent() wrapper payload shaping
# - extract_node() success path
# - extract_node() retry path
# - extract_node() human handoff path


messages = [
    HumanMessage(
        id="hm_001",
        content="I met Lucia Romero, a startup lawyer from Lima.",
    ),
    HumanMessage(
        id="hm_002",
        content="Philip de Haas now lives in Zurich.",
    ),
]


def build_plan() -> MessageSelectionOutput:
    return MessageSelectionOutput(
        reasoning_summary_for_create="Lucia Romero is a new person.",
        reasoning_summary_for_update="Philip de Haas has a location update.",
        relevant_for_create_links=[CreateLink(message_id="hm_001", new_person_count=1)],
        relevant_for_update_links=[],
    )


def build_main_state() -> MainState:
    return MainState(
        messages=messages,
        existing={
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=[],
            )
        },
        plan=build_plan(),
    )


def build_extract_state() -> ExtractAgentState:
    main = build_main_state()
    return ExtractAgentState(messages=main.messages, existing=main.existing, plan=main.plan)


class FakeExtractSubgraph:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def invoke(self, sub_state):
        self.calls.append(sub_state)
        return self.result


class FakeStructuredLLM:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        if not self.results:
            raise AssertionError("No more fake structured LLM results available.")
        return self.results.pop(0)


class FakeLLM:
    def __init__(self, results):
        self.structured_calls = []
        self.fake_structured_llm = FakeStructuredLLM(results)

    def with_structured_output(self, schema):
        self.structured_calls.append(schema)
        return self.fake_structured_llm


def test_run_extract_subagent_wrapper_filters_messages_and_plan():
    fake = FakeExtractSubgraph({"existing": {"new_001": UserProfile(name="Lucia Romero")}})
    original = graphv3.extract_subgraph
    graphv3.extract_subgraph = fake

    try:
        state = build_main_state()
        result = graphv3.run_extract_subgagent(state)

        assert "existing" in result
        assert result["existing"] == {"new_001": UserProfile(name="Lucia Romero")}
        assert len(fake.calls) == 1

        sub_state = fake.calls[0]
        assert [msg.id for msg in sub_state["messages"]] == ["hm_001"]
        assert sub_state["existing"] == {}
        assert sub_state["plan"].reasoning_summary_for_create == state.plan.reasoning_summary_for_create
        assert sub_state["plan"].relevant_for_create_links == state.plan.relevant_for_create_links
        assert sub_state["plan"].reasoning_summary_for_update == ""
        assert sub_state["plan"].relevant_for_update_links == []
    finally:
        graphv3.extract_subgraph = original


def test_extract_node_success_path():
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
        state = build_extract_state()
        state.messages = [m for m in state.messages if m.id == "hm_001"]
        state.existing = {}
        command = graphv3.extract_node(state)

        assert fake_llm.structured_calls == [UserProfileList]
        assert len(fake_llm.fake_structured_llm.calls) == 1
        assert command.goto == "__end__"
        assert "existing" in command.update
        assert len(command.update["existing"]) == 1
        created_profile = next(iter(command.update["existing"].values()))
        assert created_profile.name == "Lucia Romero"
    finally:
        graphv3.llm = original_llm


def test_extract_node_retry_then_success():
    fake_llm = FakeLLM(
        [
            UserProfileList(items=[]),
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
        ]
    )
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_extract_state()
        state.messages = [m for m in state.messages if m.id == "hm_001"]
        state.existing = {}
        command = graphv3.extract_node(state)

        assert fake_llm.structured_calls == [UserProfileList]
        assert command.goto == "__end__"
        assert len(fake_llm.fake_structured_llm.calls) == 2
        first_call = fake_llm.fake_structured_llm.calls[0]
        second_call = fake_llm.fake_structured_llm.calls[1]
        assert len(first_call) == 1 and isinstance(first_call[0], SystemMessage)
        assert len(second_call) == 1 and isinstance(second_call[0], SystemMessage)
        assert "TAKE INTO ACCOUNT THESE MESSAGE(S):" in first_call[0].content
        assert "hm_001" in first_call[0].content
        assert "The planner expected 1 new people" in second_call[0].content
        assert "hm_001" in second_call[0].content
        assert "existing" in command.update
        assert len(command.update["existing"]) == 1
    finally:
        graphv3.llm = original_llm


def test_extract_node_retry_then_handoff_to_human():
    fake_llm = FakeLLM(
        [
            UserProfileList(items=[]),
            UserProfileList(items=[]),
        ]
    )
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        state = build_extract_state()
        state.messages = [m for m in state.messages if m.id == "hm_001"]
        state.existing = {}
        command = graphv3.extract_node(state)

        assert fake_llm.structured_calls == [UserProfileList]
        assert command.goto == "human"
        assert len(fake_llm.fake_structured_llm.calls) == 2
        second_call = fake_llm.fake_structured_llm.calls[1]
        assert len(second_call) == 1 and isinstance(second_call[0], SystemMessage)
        assert "The planner expected 1 new people" in second_call[0].content
        assert "hm_001" in second_call[0].content
        assert command.update["has_create_mismatch"] is True
        assert command.update["human_prompt"] is not None
        assert "planner thought you should create" in command.update["human_prompt"]
    finally:
        graphv3.llm = original_llm
