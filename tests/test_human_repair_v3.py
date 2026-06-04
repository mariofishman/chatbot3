from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import PatchProposalList, UpdateAgentState, UserProfile


def build_state() -> UpdateAgentState:
    return UpdateAgentState(
        messages=[],
        existing={
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=["metals"],
            )
        },
        reasoning_summary_for_update="Philip de Haas has update-side changes.",
        candidate={
            "user_001": {
                "name": "Philip de Haas",
                "company": "London Metals Limited",
                "role": "Owner",
                "location": "Zurich",
                "interests": "AI hiring",
            }
        },
        errors={
            "user_001": [
                "interests: Input should be a valid list",
            ]
        },
        attempts=3,
    )


def test_route_patches_routes_to_human_repair_when_attempt_limit_is_reached():
    state = build_state()

    result = graphv3.route_patches(state)

    assert result == "human_repair"


def test_human_repair_interrupts_with_patchproposallist_shape_and_returns_patches(monkeypatch):
    state = build_state()
    captured_payloads = []

    def fake_interrupt(payload):
        captured_payloads.append(payload)
        return {
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
        }

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)

    result = graphv3.human_repair(state)

    assert len(captured_payloads) == 1
    first_payload = captured_payloads[0]
    assert "failed_candidate" in first_payload
    assert "errors" in first_payload
    assert "expected_format" in first_payload
    assert first_payload["target_id"] == "user_001"

    expected = PatchProposalList.model_validate(
        {
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
        }
    )
    assert result["patches"] == expected.items
    assert result["errors"] == {}
    assert result["attempts"] == 3


def test_human_repair_retries_until_resume_payload_matches_patchproposallist(monkeypatch):
    state = build_state()
    payloads = iter(
        [
            {"bad": "payload"},
            {
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
        ]
    )
    captured_payloads = []

    def fake_interrupt(payload):
        captured_payloads.append(payload)
        return next(payloads)

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)

    result = graphv3.human_repair(state)

    assert len(captured_payloads) == 2
    assert "Please try again." in captured_payloads[1]["message"]
    assert result["errors"] == {}
    assert result["attempts"] == 3


def test_human_repair_retries_when_patch_targets_the_wrong_user(monkeypatch):
    state = build_state()
    payloads = iter(
        [
            {
                "items": [
                    {
                        "target_id": "user_999",
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
            {
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
        ]
    )
    captured_payloads = []

    def fake_interrupt(payload):
        captured_payloads.append(payload)
        return next(payloads)

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)

    result = graphv3.human_repair(state)

    assert len(captured_payloads) == 2
    assert "Please try again." in captured_payloads[1]["message"]
    assert "target the current user id" in captured_payloads[1]["errors"][0]
    assert result["errors"] == {}
    assert result["attempts"] == 3


def test_human_repair_rejects_empty_errors():
    state = build_state()
    state.errors = {}

    with pytest.raises(ValueError) as exc_info:
        graphv3.human_repair(state)

    assert "non-empty state.errors" in str(exc_info.value)
