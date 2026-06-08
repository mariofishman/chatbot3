# Create-Then-Update Multi-Turn Integration Test Microplan

Scope: create one integration-style test file for `src/graphv3.py` that proves
the parent graph can create a profile on one turn and then update that same
profile on a later turn using the persisted thread state.

## Relevant inputs

- `src/graphv3.py`, especially:
  - compiled `graph`
  - `planner_node(...)`
  - `route_after_planner(...)`
  - `run_extract_subgagent(...)`
  - `run_update_subgagent(...)`
  - compiled `update_subgraph`
- `src/state.py`, especially:
  - `MainState`
  - `MessageSelectionOutput`
  - `CreateLink`
  - `UpdateLink`
  - `merge_profiles(...)`
- nearby tests:
  - `tests/test_create_only_path_integration_v3.py`
  - `tests/test_parent_update_path_integration_v3.py`
  - `tests/test_noop_update_integration_v3.py`

## Architecture conclusion

This test should prove a realistic threaded user flow:

1. first turn creates a new profile
2. second turn updates that same now-existing profile

Its job is to exercise the real parent graph across two invocations with the
same thread, not only isolated wrappers or subgraphs.

## What the test file must do

1. Start from an empty or near-empty `existing` state on turn 1.
2. Use one first-turn human message that should create exactly one new user.
3. Run the real parent graph for turn 1 with a fixed thread id.
4. Assert that turn 1 returns one created profile in `existing`.
5. Capture the created `user_id` from the turn-1 result.
6. Use one second-turn human message that clearly updates the created person.
7. Fake the planner-side structured outputs so:
   - turn 1 routes only to create
   - turn 2 routes only to update and targets the created `user_id`
8. Fake the create extraction output on turn 1 and the update patch output on
   turn 2.
9. Run the real parent graph again for turn 2 with the same thread id.
10. Assert that:
   - the second turn does not create a second profile for the same person
   - the second turn updates the original created profile
   - the final thread state contains the updated version of that same profile
11. Assert the state after turn 2 still contains only one profile for that
    person.

## What it must not do

- depend on live model calls
- mix a second new person into the first version
- test the human create mismatch path
- test the update repair path
- broaden into contradiction handling in the first version

## Assumptions

- the important regression here is threaded parent behavior across turns
- the first version should stay on the direct success paths for:
  - create on turn 1
  - update on turn 2
- the test should protect against accidentally duplicating a person on the
  second turn instead of updating the existing profile
