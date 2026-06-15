from pathlib import Path
import sys

from langchain_core.messages import HumanMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import MainState, SubjectBucket, SubjectBucketList, UserProfile


def new_subject(label: str, message_ids: list[str]) -> SubjectBucket:
    return SubjectBucket(
        subject_label=label,
        message_ids=message_ids,
        classification="new",
    )


def existing_subject(
    label: str,
    message_ids: list[str],
    user_id: str,
) -> SubjectBucket:
    return SubjectBucket(
        subject_label=label,
        message_ids=message_ids,
        candidate_existing_id=user_id,
        classification="existing",
    )


def message_ids(send) -> list[str]:
    return [message.id for message in send.arg["messages"]]


def test_no_subjects_route_only_to_end():
    state = MainState(messages=[], subjects=SubjectBucketList())

    assert graphv3.fan_out_creates(state) == []
    assert graphv3.fan_out_updates(state) == []
    assert graphv3.route_after_subject_planner(state) == ["__end__"]


def test_single_new_subject_produces_one_create_branch_and_route():
    subject = new_subject("Lucia", ["hm_001", "hm_002"])
    state = MainState(
        messages=[
            HumanMessage(id="hm_001", content="I met Lucia."),
            HumanMessage(id="hm_002", content="Lucia is a lawyer."),
            HumanMessage(id="hm_003", content="Unrelated message."),
        ],
        existing={"user_001": UserProfile(name="John")},
        subjects=SubjectBucketList(items=[subject]),
    )

    sends = graphv3.fan_out_creates(state)

    assert len(sends) == 1
    assert sends[0].node == "extract_subagent"
    assert sends[0].arg["subject"] == subject
    assert message_ids(sends[0]) == ["hm_001", "hm_002"]
    assert "existing" not in sends[0].arg
    assert graphv3.route_after_subject_planner(state) == sends


def test_single_existing_subject_produces_one_update_branch_and_route():
    profile = UserProfile(name="John", location="Miami")
    subject = existing_subject("John", ["hm_001"], "user_001")
    state = MainState(
        messages=[
            HumanMessage(id="hm_001", content="John moved to Miami."),
            HumanMessage(id="hm_002", content="Unrelated message."),
        ],
        existing={"user_001": profile},
        subjects=SubjectBucketList(items=[subject]),
    )

    sends = graphv3.fan_out_updates(state)

    assert len(sends) == 1
    assert sends[0].node == "update_subagent"
    assert sends[0].arg["existing"] == {"user_001": profile}
    assert message_ids(sends[0]) == ["hm_001"]
    assert "subject" not in sends[0].arg
    assert graphv3.route_after_subject_planner(state) == sends


def test_several_new_subjects_produce_one_create_branch_each():
    lucia = new_subject("Lucia", ["hm_001"])
    maria = new_subject("Maria", ["hm_002"])
    john = existing_subject("John", ["hm_003"], "user_001")
    state = MainState(
        messages=[
            HumanMessage(id="hm_001", content="I met Lucia."),
            HumanMessage(id="hm_002", content="I met Maria."),
            HumanMessage(id="hm_003", content="I spoke with John."),
        ],
        existing={"user_001": UserProfile(name="John")},
        subjects=SubjectBucketList(items=[lucia, john, maria]),
    )

    sends = graphv3.fan_out_creates(state)

    assert [send.node for send in sends] == ["extract_subagent", "extract_subagent"]
    assert [send.arg["subject"] for send in sends] == [lucia, maria]
    assert [message_ids(send) for send in sends] == [["hm_001"], ["hm_002"]]


def test_several_existing_subjects_produce_one_update_branch_each():
    john_profile = UserProfile(name="John")
    lucia_profile = UserProfile(name="Lucia")
    john = existing_subject("John", ["hm_001"], "user_001")
    lucia = existing_subject("Lucia", ["hm_002"], "user_002")
    maria = new_subject("Maria", ["hm_003"])
    state = MainState(
        messages=[
            HumanMessage(id="hm_001", content="John moved."),
            HumanMessage(id="hm_002", content="Lucia changed jobs."),
            HumanMessage(id="hm_003", content="I met Maria."),
        ],
        existing={
            "user_001": john_profile,
            "user_002": lucia_profile,
        },
        subjects=SubjectBucketList(items=[john, maria, lucia]),
    )

    sends = graphv3.fan_out_updates(state)

    assert [send.node for send in sends] == ["update_subagent", "update_subagent"]
    assert [send.arg["existing"] for send in sends] == [
        {"user_001": john_profile},
        {"user_002": lucia_profile},
    ]
    assert [message_ids(send) for send in sends] == [["hm_001"], ["hm_002"]]


def test_mixed_route_preserves_shared_and_subject_specific_evidence():
    john_profile = UserProfile(name="John")
    lucia = new_subject("Lucia", ["hm_002", "hm_001"])
    john = existing_subject("John", ["hm_003", "hm_001"], "user_001")
    state = MainState(
        messages=[
            HumanMessage(id="hm_001", content="John introduced me to Lucia."),
            HumanMessage(id="hm_002", content="Lucia is a lawyer."),
            HumanMessage(id="hm_003", content="John moved to Miami."),
            HumanMessage(id="hm_004", content="The weather is pleasant."),
        ],
        existing={"user_001": john_profile},
        subjects=SubjectBucketList(items=[lucia, john]),
    )

    destinations = graphv3.route_after_subject_planner(state)
    destinations_by_node = {
        destination.node: destination
        for destination in destinations
    }

    assert set(destinations_by_node) == {"extract_subagent", "update_subagent"}
    assert "__end__" not in destinations
    create_send = destinations_by_node["extract_subagent"]
    update_send = destinations_by_node["update_subagent"]
    assert message_ids(create_send) == ["hm_001", "hm_002"]
    assert message_ids(update_send) == ["hm_001", "hm_003"]
    assert "hm_004" not in message_ids(create_send)
    assert "hm_004" not in message_ids(update_send)
