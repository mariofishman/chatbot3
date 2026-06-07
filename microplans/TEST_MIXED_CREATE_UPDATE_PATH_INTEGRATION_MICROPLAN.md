# Mixed Create+Update Path Integration Test Microplan

Scope: create one integration-style test file for the mixed parent path in
`src/graphv3.py`, where create-side and update-side work happen in the same
planner result.

## Relevant inputs

- `src/graphv3.py`, parent-side functions:
  - `route_after_planner(...)`
  - `run_extract_subgagent(...)`
  - `run_update_subgagent(...)`
- `src/graphv3.py`, compiled `extract_subgraph`
- `src/graphv3.py`, compiled `update_subgraph`
- `src/state.py`, especially:
  - `MainState`
  - `merge_profiles(...)`
- existing integration tests:
  - `tests/test_create_only_path_integration_v3.py`
  - `tests/test_parent_update_path_integration_v3.py`

## Architecture conclusion

This test should sit one level above the separate create-only and update-only
integration tests.

Its job is to prove that the parent graph can handle a planner output that
contains both:

- create-side work
- update-side work

and that the resulting create and update outputs can be accumulated into one
final parent `existing` dict without losing either branch.

## What the test file must do

1. Build one `MainState` with:
   - at least one existing profile already in memory
   - at least three human messages:
     - one shared message that mentions both:
       - a new person to create
       - an existing person to update
     - one extra message only for the create-side person
     - one extra message only for the update-side existing person
   - a planner output whose create links and update links are both non-empty
   - create links and update links that reflect both the shared message and
     the branch-specific messages
2. Use the real `route_after_planner(...)` path and assert it returns:
   - `"extract_subagent"`
   - plus one or more `Send("update_subagent", ...)`
3. Fake the model interactions so:
   - the create branch returns one new `UserProfile`
   - the update branch returns one committed one-user update slice
4. Run the real `run_extract_subgagent(...)` wrapper for the create branch.
5. Run the real `run_update_subgagent(...)` wrapper for each update `Send(...)`
   branch.
6. Merge the resulting `existing` slices using the real reducer contract.
7. Assert the final merged parent `existing` dict contains:
   - the original existing profile updated correctly
   - the new created profile added correctly
8. Assert the shared message reaches both branches, while the branch-specific
   messages reach only their intended branch.

## What it must not do

- re-test the whole retry loop logic in detail
- depend on live model calls
- depend on the create human-handoff branch in the first version
- depend on the update human-repair branch in the first version

## Assumptions

- the create-only and update-only parent-path integrations already give
  confidence in each branch separately
- this test is about mixed composition and final parent-state accumulation
- the first version can stay on the direct success paths for both branches
