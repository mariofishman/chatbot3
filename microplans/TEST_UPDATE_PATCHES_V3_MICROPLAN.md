# Microplan For `tests/test_update_patches_v3.py`

## Scope

Create one deterministic pytest-style test file for `update_patches()` only.

## Input context to test

The test targets `update_patches(state: UpdateAgentState)` in `src/graphv3.py`.

Relevant inputs:
- `state.messages`
- `state.existing`
- `state.reasoning_summary_for_update`

## Output behavior to verify

The test file should verify that `update_patches()`:

- rejects `state.existing` with zero target profiles
- rejects `state.existing` with more than one target profile
- calls the structured-output LLM path once for a valid one-profile state
- stores the returned `PatchProposalList.items` into `patches`
- passes the mocked `PatchProposalList.items` through unchanged
- does not depend on `plan`

## Must do

- use deterministic mocks/fakes instead of a real model call
- monkeypatch the `llm.with_structured_output(...).invoke(...)` path
- assert the returned state update shape
- keep the file focused on `update_patches()` only

## Must not do

- do not test `apply_patch()`
- do not test fan-out or wrappers
- do not depend on live model output
- do not broaden into unfinished update-subgraph nodes

## Assumptions

- `update_patches()` is already implemented
- `PatchProposalList`, `PatchProposal`, `PatchOp`, `UpdateAgentState`, and `UserProfile` are stable enough to use in fixtures
- one mocked success case plus the bad-`existing` contract checks are enough for this first version
