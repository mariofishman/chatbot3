# No-Op Update Integration Test Microplan

Scope: create one integration-style test file for the parent/update path in
`src/graphv3.py` that proves a routed update branch can legitimately produce no
patches without crashing and without mutating the target profile.

## Relevant inputs

- `src/graphv3.py`, especially:
  - `planner_node(...)`
  - `route_after_planner(...)`
  - `fan_out_updates(...)`
  - `run_update_subgagent(...)`
  - compiled `update_subgraph`
  - `update_patches(...)`
  - `apply_patch(...)`
  - `validate(...)`
  - `route_patches(...)`
  - `commit(...)`
- `src/state.py`, especially:
  - `MainState`
  - `UpdateLink`
  - `MessageSelectionOutput`
  - `merge_profiles(...)`
- nearby tests:
  - `tests/test_parent_update_path_integration_v3.py`
  - `tests/test_update_subgraph_integration_v3.py`
  - `tests/test_apply_patch_v3.py`

## Architecture conclusion

This test should sit above the direct `apply_patch()` no-op unit behavior.

Its job is to prove that the real parent/update composition handles a no-op
update safely:

- the planner still routes the update branch
- the update branch may return an empty `PatchProposalList`
- the branch should not crash
- the committed result should keep the existing profile unchanged

## What the test file must do

1. Build one `MainState` with:
   - exactly one existing profile already in memory
   - one human message that mentions the existing person but does not support
     any real field change
2. Fake the planner output so the message routes into the update path for that
   one existing `user_id`.
3. Fake the model interaction inside `update_patches()` so the structured
   output is an empty `PatchProposalList`.
4. Use the real:
   - `route_after_planner(...)`
   - `fan_out_updates(...)`
   - `run_update_subgagent(...)`
   - compiled `update_subgraph`
5. Assert that:
   - the parent routing returns exactly one `Send("update_subagent", ...)`
   - the update branch completes without exception
   - the returned committed `existing` slice still contains the same user id
   - the committed profile is unchanged field-by-field
6. Assert that the final merged parent `existing` dict is unchanged.

## What it must not do

- depend on live model calls
- test the repair loop
- test human repair
- mix create-side behavior into the same file
- broaden into several no-op variants at once

## Assumptions

- empty patch output is now a valid no-op outcome, not an error
- the purpose of this test is to protect realistic parent/update composition,
  not only the low-level `apply_patch()` helper contract
- this should stay a narrow high-value regression for the manual bug already
  discovered in terminal use
