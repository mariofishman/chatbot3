from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import UpdateAgentState


def build_state() -> UpdateAgentState:
    return UpdateAgentState(
        messages=[],
        existing={},
        reasoning_summary_for_update="",
    )


def test_route_patches_returns_commit_when_errors_are_empty():
    state = build_state()
    state.errors = {}

    result = graphv3.route_patches(state)

    assert result == "commit"


def test_route_patches_returns_patch_when_errors_exist():
    state = build_state()
    state.errors = {
        "user_001": ["interests: Input should be a valid list"],
    }

    result = graphv3.route_patches(state)

    assert result == "patch"
