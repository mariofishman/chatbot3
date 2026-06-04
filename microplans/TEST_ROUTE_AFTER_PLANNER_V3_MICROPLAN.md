# Microplan For `tests/test_route_after_planner_v3.py`

## Scope

Create one deterministic pytest-style test file for `route_after_planner()` only.

## Input context to test

The test targets `route_after_planner(state: MainState)` in `src/graphv3.py`.

Relevant inputs:
- `state.plan.relevant_for_create_links`
- `state.plan.relevant_for_update_links`
- the current `fan_out_updates(...)` helper that may be called by the router

## Output behavior to verify

The test file should verify that `route_after_planner()`:

- returns only `["extract_subagent"]` when there is create work and no update work
- returns only `Send(...)` objects when there is update work and no create work
- returns both `"extract_subagent"` and `Send(...)` when both branches are needed
- returns `["__end__"]` when neither create nor update work exists
- does not mix `"__end__"` with any real branch destinations

## Must do

- use deterministic state fixtures
- keep the file focused on `route_after_planner()` only
- treat `Send(...)` objects as valid route elements, not as plain strings
- assert the returned routing list shape directly
- allow the update-route cases to use the real `fan_out_updates(...)` behavior indirectly through the router

## Must not do

- do not re-test `fan_out_updates()` payload details already covered elsewhere
- do not test wrapper behavior
- do not test planner LLM behavior
- do not broaden into full parent-graph execution

## Assumptions

- `route_after_planner()` is already implemented
- one fixture with create+update work can be reused and then narrowed into:
  - create-only
  - update-only
  - no-work
- checking the presence and types of returned route elements is enough for this first version
