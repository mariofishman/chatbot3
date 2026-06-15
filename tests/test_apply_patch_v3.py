from pprint import pprint
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from graphv3 import apply_patch
from state import PatchOp, PatchProposal, UpdateAgentState, UserProfile


# This file tests only the deterministic apply_patch() step.
#
# It does NOT test:
# - subject-planner or fanout behavior
# - Send fan-out
# - update_patches() LLM output generation
# - validate/patch/commit
#
# It only verifies that apply_patch():
# - enforces the one-profile contract
# - treats an empty patch list as a no-op update
# - applies add / replace / remove deterministically
# - writes the patched raw result into candidate


def build_state() -> UpdateAgentState:
    return UpdateAgentState(
        messages=[],
        existing={
            "user_001": UserProfile(
                name="Philip de Haas",
                company="London Metals Limited",
                role="Owner",
                location="London",
                interests=["metals", "finance"],
            )
        },
        patches=[
            PatchProposal(
                target_id="user_001",
                patches=[
                    PatchOp(op="replace", path="/location", value="Zurich"),
                    PatchOp(op="remove", path="/company"),
                    PatchOp(op="add", path="/interests/-", value="AI hiring"),
                ],
            )
        ],
    )


def test_apply_patch_happy_path():
    state = build_state()
    result = apply_patch(state)

    assert "candidate" in result
    assert "user_001" in result["candidate"]

    candidate = result["candidate"]["user_001"]
    assert candidate["location"] == "Zurich"
    assert "company" not in candidate
    assert candidate["interests"] == ["metals", "finance", "AI hiring"]

    print("\nTEST 1: apply_patch() happy path")
    pprint(candidate)


def test_apply_patch_allows_empty_patches_as_noop():
    state = build_state()
    state.patches = []

    result = apply_patch(state)
    candidate = result["candidate"]["user_001"]

    assert candidate["name"] == "Philip de Haas"
    assert candidate["company"] == "London Metals Limited"
    assert candidate["location"] == "London"
    assert candidate["interests"] == ["metals", "finance"]
    print("\nTEST 2: empty patches treated as no-op")
    pprint(candidate)


def test_apply_patch_rejects_mismatched_target():
    state = build_state()
    state.patches = [
        PatchProposal(
            target_id="user_999",
            patches=[PatchOp(op="replace", path="/location", value="Zurich")],
        )
    ]

    try:
        apply_patch(state)
    except ValueError as e:
        assert "target_id" in str(e)
        print("\nTEST 3: mismatched target_id rejected")
        print(str(e))
        return

    raise AssertionError("apply_patch() should reject mismatched patch target ids.")


def main():
    test_apply_patch_happy_path()
    test_apply_patch_allows_empty_patches_as_noop()
    test_apply_patch_rejects_mismatched_target()
    print("\nAll apply_patch() checks passed.")


if __name__ == "__main__":
    main()
