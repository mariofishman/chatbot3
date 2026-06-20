from pathlib import Path
import sys

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import PatchOp, PatchProposal, PatchProposalList, UpdateAgentState, UserProfile


def build_state() -> UpdateAgentState:
    return UpdateAgentState(
        messages=[
            HumanMessage(
                id="hm_001",
                content="Philip de Haas is also interested in AI hiring.",
            )
        ],
        existing={
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=["metals"],
            )
        },
    )


def bad_interests_patch() -> PatchProposalList:
    return PatchProposalList(
        items=[
            PatchProposal(
                target_id="user_001",
                patches=[
                    PatchOp(op="replace", path="/interests", value="AI hiring"),
                ],
            )
        ]
    )


def good_interests_submit_payload() -> dict:
    return {
        "action": "submit",
        "patches": {
            "items": [
                {
                    "target_id": "user_001",
                    "patches": [
                        {
                            "op": "replace",
                            "path": "/interests",
                            "value": ["metals", "AI hiring"],
                        }
                    ],
                }
            ]
        },
    }


def compile_checkpointed_update_subgraph():
    return graphv3.update_builder.compile(checkpointer=InMemorySaver())


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


def test_update_subgraph_retries_once_then_commits_successfully():
    fake_results = [
        PatchProposalList(
            items=[
                PatchProposal(
                    target_id="user_001",
                    patches=[
                        PatchOp(op="replace", path="/interests", value="AI hiring"),
                    ],
                )
            ]
        ),
        PatchProposalList(
            items=[
                PatchProposal(
                    target_id="user_001",
                    patches=[
                        PatchOp(
                            op="replace",
                            path="/interests",
                            value=["metals", "AI hiring"],
                        ),
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
        result = graphv3.update_subgraph.invoke(state)

        assert fake_llm.structured_calls == [PatchProposalList, PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 2

        first_call = fake_llm.fake_structured_llm.calls[0]
        second_call = fake_llm.fake_structured_llm.calls[1]
        assert len(first_call) == 1
        assert len(second_call) == 1
        assert isinstance(first_call[0], SystemMessage)
        assert isinstance(second_call[0], SystemMessage)
        assert "TARGET EXISTING PROFILE:" in first_call[0].content
        assert "FAILED RAW CANDIDATE:" in second_call[0].content
        assert "VALIDATION ERRORS:" in second_call[0].content

        assert result["attempts"] == 1
        assert result["errors"] == {}
        assert "user_001" in result["existing"]
        updated_profile = result["existing"]["user_001"]
        assert isinstance(updated_profile, UserProfile)
        assert updated_profile.interests == ["metals", "AI hiring"]
        assert updated_profile.location == "London"
    finally:
        graphv3.llm = original_llm


def test_update_subgraph_empty_patch_list_commits_unchanged_profile():
    original_profile = UserProfile(
        name="Philip de Haas",
        company="London Metals Limited",
        role="Owner",
        location="London",
        interests=["metals"],
    )
    state = UpdateAgentState(
        messages=[
            HumanMessage(
                id="hm_001",
                content="I spoke with Philip de Haas yesterday.",
            )
        ],
        existing={"user_001": original_profile},
    )
    fake_llm = FakeLLM([PatchProposalList()])
    original_llm = graphv3.llm
    graphv3.llm = fake_llm

    try:
        result = graphv3.update_subgraph.invoke(state)

        assert fake_llm.structured_calls == [PatchProposalList]
        assert len(fake_llm.fake_structured_llm.calls) == 1
        assert set(result["existing"]) == {"user_001"}
        assert result["existing"]["user_001"] == original_profile
        assert result["patches"] == []
        assert result["candidate"] == {"user_001": original_profile.model_dump()}
        assert result["errors"] == {}
        assert result["attempts"] == 0
    finally:
        graphv3.llm = original_llm


def test_update_subgraph_human_submit_commits_corrective_patches():
    fake_llm = FakeLLM([bad_interests_patch()] * 4)
    original_llm = graphv3.llm
    graphv3.llm = fake_llm
    graph = compile_checkpointed_update_subgraph()
    config = {"configurable": {"thread_id": "update-human-submit"}}

    try:
        interrupted = graph.invoke(build_state(), config=config)
        snapshot = graph.get_state(config)

        assert "__interrupt__" in interrupted
        assert len(snapshot.interrupts) == 1
        pending = snapshot.interrupts[0]
        assert pending.value["target_id"] == "user_001"
        assert snapshot.values["existing"]["user_001"].interests == ["metals"]

        result = graph.invoke(
            Command(resume={pending.id: good_interests_submit_payload()}),
            config=config,
        )

        assert graph.get_state(config).interrupts == ()
        assert result["errors"] == {}
        assert result["attempts"] == 3
        assert result["existing"]["user_001"] == UserProfile(
            name="Philip de Haas",
            company="London Metals Limited",
            role="Owner",
            location="London",
            interests=["metals", "AI hiring"],
        )
    finally:
        graphv3.llm = original_llm


def test_update_subgraph_human_decline_ends_with_original_profile_unchanged():
    original_profile = build_state().existing["user_001"]
    fake_llm = FakeLLM([bad_interests_patch()] * 4)
    original_llm = graphv3.llm
    graphv3.llm = fake_llm
    graph = compile_checkpointed_update_subgraph()
    config = {"configurable": {"thread_id": "update-human-decline"}}

    try:
        graph.invoke(build_state(), config=config)
        pending = graph.get_state(config).interrupts[0]

        result = graph.invoke(
            Command(resume={pending.id: {"action": "decline"}}),
            config=config,
        )

        assert graph.get_state(config).interrupts == ()
        assert result["patches"] == []
        assert result["existing"] == {"user_001": original_profile}
        assert result["errors"] == {
            "user_001": ["Human declined update repair."]
        }
    finally:
        graphv3.llm = original_llm


@pytest.mark.parametrize(
    "resume_payload",
    [
        {"action": "submit"},
        {"action": "submit", "patches": {"items": []}},
        {
            "action": "submit",
            "patches": {
                "items": [
                    {
                        "target_id": "user_999",
                        "patches": [
                            {
                                "op": "replace",
                                "path": "/interests",
                                "value": ["wrong target"],
                            }
                        ],
                    }
                ]
            },
        },
    ],
)
def test_update_subgraph_invalid_human_response_does_not_apply_stale_patches(
    resume_payload,
):
    original_profile = build_state().existing["user_001"]
    fake_llm = FakeLLM([bad_interests_patch()] * 4)
    original_llm = graphv3.llm
    graphv3.llm = fake_llm
    graph = compile_checkpointed_update_subgraph()
    config = {"configurable": {"thread_id": f"update-human-invalid-{hash(str(resume_payload))}"}}

    try:
        graph.invoke(build_state(), config=config)
        pending = graph.get_state(config).interrupts[0]

        result = graph.invoke(
            Command(resume={pending.id: resume_payload}),
            config=config,
        )

        assert graph.get_state(config).interrupts == ()
        assert result["patches"] == []
        assert result["existing"] == {"user_001": original_profile}
    finally:
        graphv3.llm = original_llm
