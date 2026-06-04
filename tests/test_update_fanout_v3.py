from pprint import pprint
from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
from langgraph.types import Send

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import CreateLink, MainState, MessageSelectionOutput, UpdateLink, UserProfile


# This file tests only the update-fanout architecture that now exists in
# graphv3.py. It does NOT test the internal logic of update_subgraph yet.
#
# Main goals:
# - verify that fan_out_updates() regroups update work by user_id
# - verify that each Send payload contains exactly one target profile
# - verify that each Send payload contains only the messages relevant to that
#   user
# - verify that route_after_planner() can return a mixed result containing:
#   - "extract_subagent"
#   - one or more Send("update_subagent", ...)
# - verify that run_update_subgagent() receives one-user payloads and passes
#   the expected narrower sub_state into update_subgraph
#
# This file intentionally avoids real update-subgraph logic. Instead, it uses a
# fake update_subgraph so we can inspect the payload shape first.


base_existing = {
    "user_001": UserProfile(
        name="Philip de Haas",
        company="London Metals Limited",
        role="Owner",
        location="London",
        interests=[],
    ),
    "user_002": UserProfile(
        name="Mario Fishman",
        company="Krowdy",
        role="CEO",
        location="Peru",
        interests=[],
    ),
    "user_005": UserProfile(
        name="Diego Salazar",
        company=None,
        role="Software Engineer",
        location="Arequipa",
        interests=[],
    ),
}


messages = [
    HumanMessage(id="hm_001", content="Philip de Haas now lives in Zurich."),
    HumanMessage(
        id="hm_003",
        content="Mario Fishman is focused on AI hiring, and Philip de Haas works often from Geneva.",
    ),
    HumanMessage(
        id="hm_004",
        content="I also met Lucia Romero, a startup lawyer from Lima.",
    ),
]


plan = MessageSelectionOutput(
    reasoning_summary_for_create="The last message introduces Lucia Romero as a new person.",
    reasoning_summary_for_update=(
        "Philip de Haas has location-related updates, and Mario Fishman has a work-focus update."
    ),
    relevant_for_create_links=[
        CreateLink(message_id="hm_004", new_person_count=1),
    ],
    relevant_for_update_links=[
        UpdateLink(message_id="hm_001", user_profile_ids=["user_001"]),
        UpdateLink(message_id="hm_003", user_profile_ids=["user_001", "user_002"]),
    ],
)


def make_state() -> MainState:
    return MainState(messages=messages, existing=base_existing, plan=plan)


class FakeUpdateSubgraph:
    """Capture invoke payloads so we can inspect wrapper behavior."""

    def __init__(self):
        self.calls = []

    def invoke(self, sub_state):
        self.calls.append(sub_state)
        # Return the same one-user existing payload so the reducer-facing shape
        # stays simple during this architectural test.
        return {"existing": sub_state["existing"]}


def test_fan_out_updates():
    state = make_state()
    sends = graphv3.fan_out_updates(state)

    assert isinstance(sends, list)
    assert len(sends) == 2, "Expected one Send for user_001 and one for user_002."
    assert all(isinstance(s, Send) for s in sends)
    assert all(s.node == "update_subagent" for s in sends)

    by_user = {}
    for send in sends:
        payload = send.arg
        assert "existing" in payload
        assert "messages" in payload
        assert "plan" in payload
        assert len(payload["existing"]) == 1, "Each Send should target exactly one existing profile."

        user_id = next(iter(payload["existing"].keys()))
        by_user[user_id] = payload

    # user_001 appears in two different update links, so its per-user payload
    # should carry both relevant messages.
    assert "user_001" in by_user
    assert [msg.id for msg in by_user["user_001"]["messages"]] == ["hm_001", "hm_003"]

    # user_002 appears only in hm_003, so it should receive only that message.
    assert "user_002" in by_user
    assert [msg.id for msg in by_user["user_002"]["messages"]] == ["hm_003"]

    # The wrapper currently keeps the planner object available for later use.
    assert by_user["user_001"]["plan"].reasoning_summary_for_update == plan.reasoning_summary_for_update

    print("\nTEST 1: fan_out_updates()")
    pprint(
        {
            user_id: {
                "message_ids": [m.id for m in payload["messages"]],
                "existing_ids": list(payload["existing"].keys()),
            }
            for user_id, payload in by_user.items()
        }
    )


def test_route_after_planner():
    state = make_state()
    destinations = graphv3.route_after_planner(state)

    assert isinstance(destinations, list)
    assert "extract_subagent" in destinations

    sends = [item for item in destinations if isinstance(item, Send)]
    assert len(sends) == 2, "Expected route_after_planner() to include per-user Send fan-out."

    # No __end__ should appear when there is actual create or update work.
    assert "__end__" not in destinations

    print("\nTEST 2: route_after_planner()")
    print(destinations)


def test_run_update_subagent_wrapper():
    state = make_state()
    sends = graphv3.fan_out_updates(state)

    fake = FakeUpdateSubgraph()
    original = graphv3.update_subgraph
    graphv3.update_subgraph = fake

    try:
        for send in sends:
            # MainState can be reconstructed from the Send payload because each
            # payload currently includes existing, messages, and plan.
            per_user_state = MainState(**send.arg)
            result = graphv3.run_update_subgagent(per_user_state)

            assert "existing" in result
            assert len(result["existing"]) == 1

        assert len(fake.calls) == 2, "Expected one update_subgraph.invoke() call per Send payload."

        for call in fake.calls:
            assert "messages" in call
            assert "existing" in call
            assert "reasoning_summary_for_update" in call
            assert len(call["existing"]) == 1

        print("\nTEST 3: run_update_subgagent() wrapper")
        pprint(fake.calls)
    finally:
        graphv3.update_subgraph = original


def main():
    test_fan_out_updates()
    test_route_after_planner()
    test_run_update_subagent_wrapper()
    print("\nAll update-fanout architecture checks passed.")


if __name__ == "__main__":
    main()
