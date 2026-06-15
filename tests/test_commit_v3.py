from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import UpdateAgentState, UserProfile


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
        candidate={
            "user_001": {
                "name": "Philip de Haas",
                "company": "London Metals Limited",
                "role": "Owner",
                "location": "Zurich",
                "interests": ["metals", "AI hiring"],
            }
        },
        errors={},
    )


def test_commit_happy_path_returns_one_existing_slice():
    state = build_state()

    result = graphv3.commit(state)

    assert "existing" in result
    assert list(result["existing"].keys()) == ["user_001"]
    committed_profile = result["existing"]["user_001"]
    assert isinstance(committed_profile, UserProfile)
    assert committed_profile.location == "Zurich"
    assert committed_profile.interests == ["metals", "AI hiring"]


def test_commit_rejects_non_empty_errors():
    state = build_state()
    state.errors = {"user_001": ["interests: Input should be a valid list"]}

    with pytest.raises(ValueError) as exc_info:
        graphv3.commit(state)

    assert "empty state.errors" in str(exc_info.value)


def test_commit_rejects_mismatched_candidate_id():
    state = build_state()
    state.candidate = {"user_999": state.candidate["user_001"]}

    with pytest.raises(ValueError) as exc_info:
        graphv3.commit(state)

    assert "candidate_id" in str(exc_info.value)


def test_commit_rejects_non_dict_candidate_payload():
    state = build_state()
    state.candidate = {"user_001": "not a raw dict"}

    with pytest.raises(ValueError) as exc_info:
        graphv3.commit(state)

    assert "raw dict" in str(exc_info.value)
