from pathlib import Path
import sys
import uuid

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import ExtractAgentState, MessageSelectionOutput


def build_state() -> ExtractAgentState:
    return ExtractAgentState(
        messages=[],
        existing={},
        plan=MessageSelectionOutput(
            reasoning_summary_for_create="",
            reasoning_summary_for_update="",
            relevant_for_create_links=[],
            relevant_for_update_links=[],
        ),
        human_prompt="Please provide the missing profiles in UserProfileList JSON format.",
    )


def test_human_accepts_valid_payload_first_try(monkeypatch):
    calls = []
    state = build_state()
    valid_payload = {
        "items": [
            {
                "name": "Lucia Romero",
                "company": None,
                "role": "Startup Lawyer",
                "location": "Lima",
                "interests": [],
            }
        ]
    }

    def fake_interrupt(payload):
        calls.append(payload)
        return valid_payload

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)
    monkeypatch.setattr(
        graphv3.uuid,
        "uuid4",
        lambda: uuid.UUID("00000000-0000-0000-0000-000000000001"),
    )

    result = graphv3.human(state)

    assert calls == [state.human_prompt]
    assert list(result.keys()) == ["existing"]
    assert list(result["existing"].keys()) == ["00000000-0000-0000-0000-000000000001"]

    created = result["existing"]["00000000-0000-0000-0000-000000000001"]
    assert created.name == "Lucia Romero"
    assert created.company is None
    assert created.role == "Startup Lawyer"
    assert created.location == "Lima"
    assert created.interests == []


def test_human_retries_after_invalid_payload(monkeypatch):
    calls = []
    state = build_state()
    payloads = iter(
        [
            {"bad": "shape"},
            {
                "items": [
                    {
                        "name": "Lucia Romero",
                        "company": None,
                        "role": "Startup Lawyer",
                        "location": "Lima",
                        "interests": [],
                    }
                ]
            },
        ]
    )

    def fake_interrupt(payload):
        calls.append(payload)
        return next(payloads)

    monkeypatch.setattr(graphv3, "interrupt", fake_interrupt)
    monkeypatch.setattr(
        graphv3.uuid,
        "uuid4",
        lambda: uuid.UUID("00000000-0000-0000-0000-000000000002"),
    )

    result = graphv3.human(state)

    assert len(calls) == 2
    assert calls[0] == state.human_prompt

    retry_payload = calls[1]
    assert isinstance(retry_payload, dict)
    assert (
        retry_payload["message"]
        == "The payload did not match the expected UserProfileList JSON shape. Please try again."
    )
    assert retry_payload["errors"]
    assert "expected_format" in retry_payload
    assert retry_payload["expected_format"]["items"][0]["name"] == "Lucia Romero"

    assert list(result["existing"].keys()) == ["00000000-0000-0000-0000-000000000002"]
    created = result["existing"]["00000000-0000-0000-0000-000000000002"]
    assert created.name == "Lucia Romero"
    assert created.company is None
    assert created.role == "Startup Lawyer"
    assert created.location == "Lima"
    assert created.interests == []
