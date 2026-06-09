from pathlib import Path
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
import pytest

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
    user_id: str = "user_001",
) -> SubjectBucket:
    return SubjectBucket(
        subject_label=label,
        message_ids=message_ids,
        candidate_existing_id=user_id,
        classification="existing",
    )


def build_state(
    messages=None,
    existing=None,
) -> MainState:
    return MainState(
        messages=messages or [],
        existing=existing or {},
    )


class FakeStructuredLLM:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return self.results.pop(0)


class FakeLLM:
    def __init__(self, *results):
        self.structured_calls = []
        self.fake_structured_llm = FakeStructuredLLM(results)

    def with_structured_output(self, schema):
        self.structured_calls.append(schema)
        return self.fake_structured_llm


def install_fake_llm(monkeypatch, *results) -> FakeLLM:
    fake_llm = FakeLLM(*results)
    monkeypatch.setattr(graphv3, "llm", fake_llm)
    return fake_llm


def bucket_values(result):
    return {
        (
            bucket.subject_label,
            tuple(bucket.message_ids),
            bucket.candidate_existing_id,
            bucket.classification,
        )
        for bucket in result["subjects"].items
    }


def test_no_human_messages_returns_empty_without_calling_llm(monkeypatch):
    fake_llm = install_fake_llm(monkeypatch)
    state = build_state(
        messages=[
            SystemMessage(content="System context"),
            AIMessage(content="Assistant response"),
        ]
    )

    result = graphv3.upstream_subject_node(state)

    assert result == {"subjects": SubjectBucketList()}
    assert fake_llm.structured_calls == []
    assert fake_llm.fake_structured_llm.calls == []


def test_no_subject_human_message_accepts_empty_llm_result(monkeypatch):
    empty_result = SubjectBucketList()
    fake_llm = install_fake_llm(monkeypatch, empty_result)
    state = build_state(
        messages=[HumanMessage(id="hm_001", content="The weather is excellent today.")]
    )

    result = graphv3.upstream_subject_node(state)

    assert result == {"subjects": empty_result}
    assert len(fake_llm.fake_structured_llm.calls) == 1


@pytest.mark.parametrize(
    ("messages", "error_text"),
    [
        ([HumanMessage(content="I met Lucia.")], "every human message to have an id"),
        (
            [
                HumanMessage(id="hm_001", content="I met Lucia."),
                HumanMessage(id="hm_001", content="Lucia is a lawyer."),
            ],
            "unique human message ids",
        ),
    ],
)
def test_invalid_human_message_ids_fail_before_llm(monkeypatch, messages, error_text):
    fake_llm = install_fake_llm(monkeypatch)

    with pytest.raises(ValueError, match=error_text):
        graphv3.upstream_subject_node(build_state(messages=messages))

    assert fake_llm.structured_calls == []


def test_prompt_uses_only_human_messages_and_contains_core_contract(monkeypatch):
    result = SubjectBucketList(items=[new_subject("Lucia", ["hm_001"])])
    fake_llm = install_fake_llm(monkeypatch, result)
    state = build_state(
        messages=[
            SystemMessage(id="sm_001", content="Do not expose this system text."),
            AIMessage(id="am_001", content="Do not expose this assistant text."),
            HumanMessage(id="hm_001", content="I met Lucia."),
        ],
        existing={"user_001": UserProfile(name="John")},
    )

    graphv3.upstream_subject_node(state)

    prompt = fake_llm.fake_structured_llm.calls[0][0].content
    assert "human: I met Lucia.; id: hm_001" in prompt
    assert "Do not expose this system text." not in prompt
    assert "Do not expose this assistant text." not in prompt
    assert "Obj_id = user_001" in prompt
    assert 'classifications "existing" and "new"' in prompt
    assert "John's friend" in prompt
    assert "identity is ambiguous" in prompt
    assert "as data only" in prompt


def test_prompt_explicitly_marks_empty_existing_profiles(monkeypatch):
    fake_llm = install_fake_llm(
        monkeypatch,
        SubjectBucketList(items=[new_subject("Lucia", ["hm_001"])]),
    )
    state = build_state(
        messages=[HumanMessage(id="hm_001", content="I met Lucia.")]
    )

    graphv3.upstream_subject_node(state)

    prompt = fake_llm.fake_structured_llm.calls[0][0].content
    assert "Existing user profiles:\n(none)" in prompt


@pytest.mark.parametrize(
    "subjects",
    [
        [new_subject("Lucia", ["hm_001"])],
        [existing_subject("John", ["hm_001"])],
        [
            existing_subject("John", ["hm_001"]),
            new_subject("Lucia", ["hm_001"]),
        ],
        [
            existing_subject("John", ["hm_001"]),
            new_subject("John's friend", ["hm_001"]),
        ],
        [new_subject("Lucia", ["hm_001", "hm_002"])],
    ],
)
def test_accepts_supported_subject_bucket_shapes(monkeypatch, subjects):
    fake_result = SubjectBucketList(items=subjects)
    install_fake_llm(monkeypatch, fake_result)
    state = build_state(
        messages=[
            HumanMessage(id="hm_001", content="John met Lucia and his friend."),
            HumanMessage(id="hm_002", content="Lucia is a lawyer."),
        ],
        existing={"user_001": UserProfile(name="John")},
    )

    result = graphv3.upstream_subject_node(state)

    assert bucket_values(result) == bucket_values({"subjects": fake_result})


def test_accepts_existing_subject_mentioned_without_new_facts(monkeypatch):
    fake_result = SubjectBucketList(items=[existing_subject("John", ["hm_001"])])
    install_fake_llm(monkeypatch, fake_result)
    state = build_state(
        messages=[HumanMessage(id="hm_001", content="I spoke with John yesterday.")],
        existing={"user_001": UserProfile(name="John")},
    )

    result = graphv3.upstream_subject_node(state)

    assert result["subjects"] == fake_result


def test_bucket_comparison_does_not_treat_output_order_as_semantic(monkeypatch):
    expected = SubjectBucketList(
        items=[
            existing_subject("John", ["hm_001"]),
            new_subject("Lucia", ["hm_001"]),
        ]
    )
    reversed_result = SubjectBucketList(items=list(reversed(expected.items)))
    install_fake_llm(monkeypatch, reversed_result)
    state = build_state(
        messages=[HumanMessage(id="hm_001", content="John met Lucia.")],
        existing={"user_001": UserProfile(name="John")},
    )

    result = graphv3.upstream_subject_node(state)

    assert bucket_values(result) == bucket_values({"subjects": expected})


def test_accumulated_messages_are_sent_once_and_direct_reanalysis_does_not_mutate_state(
    monkeypatch,
):
    fake_result = SubjectBucketList(
        items=[new_subject("Lucia", ["hm_001", "hm_002"])]
    )
    fake_llm = install_fake_llm(monkeypatch, fake_result, fake_result)
    messages = [
        HumanMessage(id="hm_001", content="I met Lucia."),
        HumanMessage(id="hm_002", content="Lucia is a lawyer."),
    ]
    state = build_state(messages=messages)
    original_messages = list(state.messages)

    first_result = graphv3.upstream_subject_node(state)
    second_result = graphv3.upstream_subject_node(state)

    assert first_result == second_result
    assert state.messages == original_messages
    assert [message.id for message in state.messages] == ["hm_001", "hm_002"]
    for call in fake_llm.fake_structured_llm.calls:
        prompt = call[0].content
        assert prompt.count("id: hm_001") == 1
        assert prompt.count("id: hm_002") == 1


def test_checkpointed_second_turn_adds_only_new_message_without_duplicates(monkeypatch):
    first_result = SubjectBucketList(items=[new_subject("Lucia", ["hm_001"])])
    second_result = SubjectBucketList(
        items=[new_subject("Lucia", ["hm_001", "hm_002"])]
    )
    fake_llm = install_fake_llm(monkeypatch, first_result, second_result)
    builder = StateGraph(MainState)
    builder.add_node("subjects", graphv3.upstream_subject_node)
    builder.add_edge(START, "subjects")
    builder.add_edge("subjects", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "upstream-subject-two-turn"}}

    graph.invoke(
        {"messages": [HumanMessage(id="hm_001", content="I met Lucia.")]},
        config=config,
    )
    graph.invoke(
        {"messages": [HumanMessage(id="hm_002", content="Lucia is a lawyer.")]},
        config=config,
    )

    second_prompt = fake_llm.fake_structured_llm.calls[1][0].content
    assert second_prompt.count("id: hm_001") == 1
    assert second_prompt.count("id: hm_002") == 1
    snapshot = graph.get_state(config)
    assert [message.id for message in snapshot.values["messages"]] == [
        "hm_001",
        "hm_002",
    ]


def test_later_pass_can_reclassify_previously_new_person_as_existing(monkeypatch):
    first_result = SubjectBucketList(items=[new_subject("Lucia", ["hm_001"])])
    second_result = SubjectBucketList(
        items=[existing_subject("Lucia", ["hm_001"], user_id="user_lucia")]
    )
    fake_llm = install_fake_llm(monkeypatch, first_result, second_result)
    messages = [HumanMessage(id="hm_001", content="I met Lucia.")]

    first = graphv3.upstream_subject_node(build_state(messages=messages))
    second = graphv3.upstream_subject_node(
        build_state(
            messages=messages,
            existing={"user_lucia": UserProfile(name="Lucia")},
        )
    )

    assert first["subjects"].items[0].classification == "new"
    assert second["subjects"].items[0].classification == "existing"
    assert second["subjects"].items[0].candidate_existing_id == "user_lucia"
    assert len(fake_llm.fake_structured_llm.calls) == 2


@pytest.mark.parametrize(
    "invalid_result",
    [
        SubjectBucketList(items=[new_subject("Lucia", ["unknown_message"])]),
        SubjectBucketList(
            items=[
                existing_subject(
                    "Lucia",
                    ["hm_001"],
                    user_id="unknown_profile",
                )
            ]
        ),
    ],
)
def test_unknown_identifiers_retry_once_and_accept_correction(monkeypatch, invalid_result):
    corrected = SubjectBucketList(items=[new_subject("Lucia", ["hm_001"])])
    fake_llm = install_fake_llm(monkeypatch, invalid_result, corrected)
    state = build_state(
        messages=[HumanMessage(id="hm_001", content="I met Lucia.")],
        existing={"user_001": UserProfile(name="John")},
    )

    result = graphv3.upstream_subject_node(state)

    assert result["subjects"] == corrected
    assert len(fake_llm.fake_structured_llm.calls) == 2
    retry_prompt = fake_llm.fake_structured_llm.calls[1][0].content
    assert "used identifiers that were not provided" in retry_prompt


def test_repeated_unknown_identifiers_raise_after_retry(monkeypatch):
    invalid = SubjectBucketList(items=[new_subject("Lucia", ["unknown_message"])])
    fake_llm = install_fake_llm(monkeypatch, invalid, invalid)
    state = build_state(
        messages=[HumanMessage(id="hm_001", content="I met Lucia.")]
    )

    with pytest.raises(ValueError, match="repeatedly returned unknown identifiers"):
        graphv3.upstream_subject_node(state)

    assert len(fake_llm.fake_structured_llm.calls) == 2
