from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import UpdateAgentState


def build_state() -> UpdateAgentState:
    return UpdateAgentState(
        messages=[],
        existing={},
        candidate={
            "user_001": {
                "name": "Philip de Haas",
                "company": "London Metals Limited",
                "role": "Owner",
                "location": "Zurich",
                "interests": ["metals", "finance"],
            }
        },
    )


def test_validate_happy_path_returns_empty_errors():
    state = build_state()

    result = graphv3.validate(state)

    assert result == {"errors": {}}


def test_validate_returns_reconstruction_errors_for_invalid_profile_type():
    state = build_state()
    state.candidate["user_001"]["interests"] = "finance"

    result = graphv3.validate(state)

    assert "errors" in result
    assert "user_001" in result["errors"]
    assert any("interests" in error for error in result["errors"]["user_001"])


def test_validate_rejects_zero_candidates():
    state = build_state()
    state.candidate = {}

    with pytest.raises(ValueError) as exc_info:
        graphv3.validate(state)

    assert "exactly one candidate profile" in str(exc_info.value)


def test_validate_rejects_non_dict_candidate_payload():
    state = build_state()
    state.candidate = {"user_001": "not a profile dict"}

    with pytest.raises(ValueError) as exc_info:
        graphv3.validate(state)

    assert "raw dict payload" in str(exc_info.value)
