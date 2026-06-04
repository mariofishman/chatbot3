from pathlib import Path
import sys

from langchain_core.messages import HumanMessage
from langgraph.types import Send

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import CreateLink, MainState, MessageSelectionOutput, UpdateLink, UserProfile


# This file tests only route_after_planner().
#
# It does NOT test:
# - planner LLM behavior
# - wrapper behavior
# - update_subgraph internals
# - fan_out_updates() payload details beyond the router contract
#
# It verifies that route_after_planner():
# - returns create-only routing correctly
# - returns update-only Send routing correctly
# - returns mixed create + update routing correctly
# - returns __end__ when there is no work


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


def build_state(plan: MessageSelectionOutput) -> MainState:
    return MainState(messages=messages, existing=base_existing, plan=plan)


def test_route_after_planner_create_only():
    plan = MessageSelectionOutput(
        reasoning_summary_for_create="Lucia Romero is a new person.",
        reasoning_summary_for_update="",
        relevant_for_create_links=[CreateLink(message_id="hm_004", new_person_count=1)],
        relevant_for_update_links=[],
    )

    state = build_state(plan)
    destinations = graphv3.route_after_planner(state)

    assert destinations == ["extract_subagent"]
    assert not any(isinstance(item, Send) for item in destinations)


def test_route_after_planner_update_only():
    plan = MessageSelectionOutput(
        reasoning_summary_for_create="",
        reasoning_summary_for_update="Philip de Haas and Mario Fishman have updates.",
        relevant_for_create_links=[],
        relevant_for_update_links=[
            UpdateLink(message_id="hm_001", user_profile_ids=["user_001"]),
            UpdateLink(message_id="hm_003", user_profile_ids=["user_001", "user_002"]),
        ],
    )

    state = build_state(plan)
    destinations = graphv3.route_after_planner(state)

    assert isinstance(destinations, list)
    assert destinations
    assert all(isinstance(item, Send) for item in destinations)
    assert all(item.node == "update_subagent" for item in destinations)
    assert "__end__" not in destinations
    assert len(destinations) == 2


def test_route_after_planner_mixed():
    plan = MessageSelectionOutput(
        reasoning_summary_for_create="Lucia Romero is a new person.",
        reasoning_summary_for_update="Philip de Haas and Mario Fishman have updates.",
        relevant_for_create_links=[CreateLink(message_id="hm_004", new_person_count=1)],
        relevant_for_update_links=[
            UpdateLink(message_id="hm_001", user_profile_ids=["user_001"]),
            UpdateLink(message_id="hm_003", user_profile_ids=["user_001", "user_002"]),
        ],
    )

    state = build_state(plan)
    destinations = graphv3.route_after_planner(state)

    assert "extract_subagent" in destinations
    sends = [item for item in destinations if isinstance(item, Send)]
    assert len(sends) == 2
    assert all(item.node == "update_subagent" for item in sends)
    assert "__end__" not in destinations
    assert len(destinations) == 3


def test_route_after_planner_no_work():
    plan = MessageSelectionOutput(
        reasoning_summary_for_create="",
        reasoning_summary_for_update="",
        relevant_for_create_links=[],
        relevant_for_update_links=[],
    )

    state = build_state(plan)
    destinations = graphv3.route_after_planner(state)

    assert destinations == ["__end__"]
