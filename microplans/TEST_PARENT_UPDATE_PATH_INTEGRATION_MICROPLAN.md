# Parent Update Path Integration Test Microplan

Scope: create one integration-style test file for the parent update path in
`src/graphv3.py`.

## Relevant inputs

- `src/graphv3.py`, parent-side functions:
  - `route_after_planner(...)`
  - `fan_out_updates(...)`
  - `run_update_subgagent(...)`
- `src/graphv3.py`, compiled `update_subgraph`
- `src/state.py`, especially:
  - `MainState`
  - `UpdateAgentState`
  - `merge_profiles(...)`
- existing focused tests:
  - `tests/test_update_fanout_v3.py`
  - `tests/test_update_subgraph_integration_v3.py`

## Architecture conclusion

This test should sit one level above the one-user `update_subgraph`
integration test.

Its job is to prove that the parent update path can:

- route a mixed update plan into more than one per-user `Send(...)`
- run each one-user update branch through `run_update_subgagent(...)`
- merge the committed one-user results back into parent `existing`

The first version should already cover the stronger shared-message case:

- one single human message mentions updates for more than one user
- the parent fan-out should give that same message to multiple one-user
  update branches
- each branch should still commit only its own profile correctly
- at least one user should also have an additional user-specific message so
  the test proves fan-out can combine:
  - shared messages
  - plus user-only messages

## What the test file must do

1. Build one `MainState` with:
   - at least two existing profiles
   - at least two human messages
   - a planner output whose update links target more than one user
   - at least one update link where a single message id points to more than
     one user id
   - at least one second update link that belongs to only one of those users
2. Use the real `route_after_planner(...)` and `fan_out_updates(...)` path to
   obtain the per-user update `Send(...)` payloads.
3. Fake the model interactions so each one-user subgraph run is deterministic.
4. Run the real `run_update_subgagent(...)` wrapper for each `Send(...)`
   payload.
5. Merge the returned committed `existing` slices using the real reducer
   contract.
6. Assert that the final merged parent `existing` dict contains both updated
   profiles correctly.
7. Assert that the shared message is present in each relevant one-user branch.
8. Assert that a user-specific message appears only in the intended one-user
   branch.

## What it must not do

- re-test every internal node already covered by unit tests
- depend on create-side routing in the first version
- depend on live model calls
- try to test the human-repair branch in the first version

## Assumptions

- `update_subgraph` is already integration-tested for the one-user retry loop
- this test is about parent composition and reducer behavior across multiple
  one-user update runs
- the first version can stay focused on update-only parent routing, not mixed
  create+update behavior
