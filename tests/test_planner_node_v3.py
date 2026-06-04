from pathlib import Path
import sys

from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import CreateLink, MainState, MessageSelectionOutput, UpdateLink, UserProfile


def build_state() -> MainState:
    return MainState(
        messages=[
            HumanMessage(
                content="Philip de Haas now lives in Zurich and I also met Lucia Romero.",
                id="hm_001",
            )
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
        plan=None,
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


def test_planner_node_stores_structured_result_and_builds_expected_prompt(monkeypatch):
    fake_result = MessageSelectionOutput(
        reasoning_summary_for_create="Lucia Romero is a new person.",
        reasoning_summary_for_update="Philip de Haas has a location update.",
        relevant_for_create_links=[CreateLink(message_id="hm_001", new_person_count=1)],
        relevant_for_update_links=[UpdateLink(message_id="hm_001", user_profile_ids=["user_001"])],
    )
    fake_llm = FakeLLM(fake_result)
    monkeypatch.setattr(graphv3, "llm", fake_llm)

    state = build_state()
    result = graphv3.planner_node(state)

    assert result == {"plan": fake_result}
    assert fake_llm.structured_calls == [MessageSelectionOutput]
    assert len(fake_llm.fake_structured_llm.calls) == 1

    llm_call = fake_llm.fake_structured_llm.calls[0]
    assert len(llm_call) == 1 + len(state.messages)
    assert isinstance(llm_call[0], SystemMessage)
    assert llm_call[1:] == state.messages
    assert llm_call[1] is state.messages[0]

    prompt = llm_call[0].content
    assert "Existing profiles:" in prompt
    assert "Existing messages:" in prompt
    assert "Obj_id = user_001" in prompt
    assert "name : Philip de Haas" in prompt
    assert "human: Philip de Haas now lives in Zurich and I also met Lucia Romero.; id: hm_001" in prompt
