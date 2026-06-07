# Update Subgraph Integration Test Microplan

Scope: create one integration-style test file for the whole `update_subgraph`
in `src/graphv3.py`.

## Relevant inputs

- `src/graphv3.py`, compiled `update_subgraph`
- update-subgraph nodes:
  - `update_patches(...)`
  - `apply_patch(...)`
  - `validate(...)`
  - `route_patches(...)`
  - `patch(...)`
  - `human_repair(...)`
  - `commit(...)`
- existing focused tests for the individual nodes

## Architecture conclusion

This test should not replace the unit tests.

Its job is to prove that the node-level contracts actually compose into a
working update loop when the compiled `update_subgraph` runs as a graph.

The first integration target should stay small:

- one target profile
- one invalid first patch proposal
- one corrective retry patch proposal
- successful final commit

## What the test file must do

1. Build one `UpdateAgentState` input with:
   - one target profile in `existing`
   - one or more update-relevant messages
   - one update summary
2. Fake the model interactions so the subgraph runs deterministically:
   - first `update_patches(...)` call returns a bad patch set
   - later `patch(...)` call returns a corrected patch set
3. Run the real compiled `update_subgraph`.
4. Assert that the graph goes through the intended retry path:
   - initial patch application fails validation
   - `route_patches(...)` sends control to `patch(...)`
   - corrected patches are applied
   - validation passes
   - `commit(...)` returns the final one-user `existing` slice
5. Assert the final committed `UserProfile` contains the corrected update.

## What it must not do

- re-test every small helper already covered by unit tests
- depend on live model calls
- depend on the human-repair branch in the first version
- verify internal LangGraph mechanics beyond the branch outcome we need

## Assumptions

- the node-level unit tests already give confidence in local behavior
- this test is only about composition of the retry loop
- the first version can ignore `human_repair(...)` and cover only:
  - `update_patches`
  - `apply_patch`
  - `validate`
  - `route_patches`
  - `patch`
  - `commit`
