from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import PatchProposalList, UpdateAgentState, UserProfile


def build_state(**overrides) -> UpdateAgentState:
    state_data = {
        "messages": [],
        "existing": {
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=["metals"],
            )
        },
        "candidate": {
            "user_001": {
                "name": "Philip de Haas",
                "company": "London Metals Limited",
                "role": "Owner",
                "location": "Zurich",
                "interests": "AI hiring",
            }
        },
        "errors": {
            "user_001": [
                "interests: Input should be a valid list",
            ]
        },
        "attempts": 3,
    }
    state_data.update(overrides)
    return UpdateAgentState(**state_data)


def submit_payload(target_id: str = "user_001") -> dict:
    return {
        "action": "submit",
        "patches": {
            "items": [
                {
                    "target_id": target_id,
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


def test_route_patches_routes_to_human_repair_when_attempt_limit_is_reached():
    state = build_state()

    result = graphv3.route_patches(state)

    assert result == "human_repair"


def test_human_repair_submit_envelope_returns_patches_and_routes_to_apply_patch(
    monkeypatch,
):
    state = build_state()
    captured_payloads = []

    def fake_interrupt(payload):
        captured_payloads.append(payload)
        return submit_payload()

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)

    result = graphv3.human_repair(state)

    assert len(captured_payloads) == 1
    first_payload = captured_payloads[0]
    assert "failed_candidate" in first_payload
    assert "errors" in first_payload
    assert first_payload["target_id"] == "user_001"
    assert first_payload["response_instruction"] == (
        "Resume with exactly one of these response examples."
    )
    assert first_payload["response_examples"][0]["action"] == "submit"
    assert first_payload["response_examples"][1] == {"action": "decline"}

    expected = PatchProposalList.model_validate(submit_payload()["patches"])
    assert result["patches"] == expected.items
    assert result["errors"] == {}
    assert result["attempts"] == 3
    assert graphv3.route_after_human_repair(
        build_state(patches=result["patches"], errors=result["errors"])
    ) == "apply_patch"


def test_human_repair_decline_returns_no_patches_and_routes_to_end(monkeypatch):
    state = build_state()
    captured_payloads = []

    def fake_interrupt(payload):
        captured_payloads.append(payload)
        return {"action": "decline"}

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)

    result = graphv3.human_repair(state)

    assert len(captured_payloads) == 1
    assert result["patches"] == []
    assert result["errors"] == {"user_001": ["Human declined update repair."]}
    assert result["attempts"] == 3
    assert graphv3.route_after_human_repair(
        build_state(patches=result["patches"], errors=result["errors"])
    ) == "__end__"


@pytest.mark.parametrize(
    ("resume_payload", "expected_error"),
    [
        (
            "not a dict",
            "Human update-repair response must be an action envelope.",
        ),
        (
            {},
            "Human update-repair response requires action='submit' or 'decline'.",
        ),
        (
            {"action": "retry"},
            "Human update-repair response requires action='submit' or 'decline'.",
        ),
        (
            {"action": "submit"},
            "Input should be a valid dictionary or instance of PatchProposalList",
        ),
        (
            {"action": "submit", "patches": {"items": []}},
            "At least one PatchProposal must be provided for human repair.",
        ),
        (
            submit_payload("user_999"),
            "All human repair PatchProposals must target the current user id.",
        ),
    ],
)
def test_human_repair_malformed_responses_return_no_patches_and_route_to_end(
    monkeypatch,
    resume_payload,
    expected_error,
):
    state = build_state()
    captured_payloads = []

    def fake_interrupt(payload):
        captured_payloads.append(payload)
        return resume_payload

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)

    result = graphv3.human_repair(state)

    assert len(captured_payloads) == 1
    assert result["patches"] == []
    assert result["attempts"] == 3
    assert any(
        expected_error in error for error in result["errors"]["user_001"]
    )
    assert graphv3.route_after_human_repair(
        build_state(patches=result["patches"], errors=result["errors"])
    ) == "__end__"


@pytest.mark.parametrize(
    ("overrides", "expected_error"),
    [
        ({"errors": {}}, "non-empty state.errors"),
        ({"existing": {}}, "exactly one target profile"),
        ({"candidate": {}}, "exactly one raw candidate profile"),
        (
            {
                "candidate": {
                    "user_999": {
                        "name": "Philip de Haas",
                        "interests": "AI hiring",
                    }
                }
            },
            "candidate_id=user_999",
        ),
    ],
)
def test_human_repair_invalid_preconditions_fail_clearly(
    overrides,
    expected_error,
):
    state = build_state(**overrides)

    with pytest.raises(ValueError, match=expected_error):
        graphv3.human_repair(state)


def test_route_after_human_repair_rejects_patches_with_errors():
    state = build_state(patches=PatchProposalList.model_validate(
        submit_payload()["patches"]
    ).items)

    with pytest.raises(ValueError, match="cannot apply patches"):
        graphv3.route_after_human_repair(state)
