from pprint import pprint
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from graphv3 import apply_patch
from state import PatchOp, PatchProposal, UpdateAgentState, UserProfile


# This file tests only the deterministic apply_patch() step.
#
# It does NOT test:
# - planner behavior
# - Send fan-out
# - update_patches() LLM output generation
# - validate/patch/commit
#
# It only verifies that apply_patch():
# - enforces the one-profile contract
# - requires at least one PatchProposal
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
        reasoning_summary_for_update="Philip de Haas has location and interest updates.",
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
    assert candidate["company"] is None
    assert candidate["interests"] == ["metals", "finance", "AI hiring"]

    print("\nTEST 1: apply_patch() happy path")
    pprint(candidate)


def test_apply_patch_rejects_empty_patches():
    state = build_state()
    state.patches = []

    try:
        apply_patch(state)
    except ValueError as e:
        assert "at least one PatchProposal" in str(e)
        print("\nTEST 2: empty patches rejected")
        print(str(e))
        return

    raise AssertionError("apply_patch() should reject empty state.patches.")


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
    test_apply_patch_rejects_empty_patches()
    test_apply_patch_rejects_mismatched_target()
    print("\nAll apply_patch() checks passed.")


if __name__ == "__main__":
    main()
