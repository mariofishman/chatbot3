# Create-Only Path Integration Test Microplan

Scope: create one integration-style test file for the create-only parent path
in `src/graphv3.py`.

## Relevant inputs

- `src/graphv3.py`, parent-side functions:
  - `route_after_planner(...)`
  - `run_extract_subgagent(...)`
- `src/graphv3.py`, compiled `extract_subgraph`
- `src/state.py`, especially:
  - `MainState`
  - `ExtractAgentState`
- existing focused tests:
  - `tests/test_extract_subagent_v3.py`
  - `tests/test_human_v3.py`

## Architecture conclusion

This test should sit one level above the create-side unit tests.

Its job is to prove that the parent create path can:

- route create-only planner output to `extract_subagent`
- run the real `run_extract_subgagent(...)` wrapper
- go through the real compiled `extract_subgraph`
- return new committed `existing` profiles from the create path

## What the test file must do

1. Build one `MainState` with:
   - at least one existing profile already in memory
   - at least two human messages:
     - one that introduces a new person
     - one that is irrelevant to the create path or only update-relevant
   - a planner output whose create links are non-empty and whose update links
     are empty
2. Use the real `route_after_planner(...)` path and assert it returns only
   `"extract_subagent"`.
3. Fake the create-side model interaction so the compiled `extract_subgraph`
   runs deterministically.
4. Run the real `run_extract_subgagent(...)` wrapper.
5. Assert the returned `existing` slice contains the newly created profile.
6. Assert the existing old profile is not passed into the extract subgraph
   working state.
7. Assert only the create-relevant message(s) are passed into the extract
   subgraph working state.
8. Assert the route result does not include `Send(...)` destinations or
   `"__end__"`.

## What it must not do

- depend on update-side routing in the first version
- depend on live model calls
- depend on the human-handoff branch in the first version
- re-test every small create-side unit behavior already covered elsewhere

## Assumptions

- the create-side nodes are already unit-tested
- this test is about parent composition of the create-only branch
- the first version can stay on the direct success path, without forcing the
  retry or human-handoff branch
