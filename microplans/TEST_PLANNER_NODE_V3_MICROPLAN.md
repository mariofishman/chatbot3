# Test Planner Node V3 Microplan

Scope: create `tests/test_planner_node_v3.py` only.

## Relevant inputs

- `microplans/SUITE_TESTS.md`, target `2. planner_node`
- `src/graphv3.py`, function `planner_node(state: MainState)`
- `src/state.py`, models:
  - `MainState`
  - `MessageSelectionOutput`
  - `CreateLink`
  - `UpdateLink`
  - `UserProfile`

## What this test file should cover

1. `planner_node(...)` stores the structured LLM result directly into
   `plan`.
2. The prompt path is exercised with a fake structured LLM.
3. The prompt includes the formatted existing profiles and the formatted
   messages.
4. The LLM call shape is correct:
   - first item is the planner `SystemMessage`
   - then the original state messages are passed through unchanged

## How the test should be built

- Use deterministic tests with a fake `llm`.
- Monkeypatch `graphv3.llm` so
  `llm.with_structured_output(MessageSelectionOutput)` returns a fake object
  whose `invoke(...)` captures the messages it receives.
- Build a small `MainState` fixture with:
  - at least one existing profile
  - at least one human message with an id

## What the tests should assert

- The returned dict is exactly `{"plan": fake_result}`.
- `with_structured_output(...)` is called with `MessageSelectionOutput`.
- The fake `invoke(...)` receives:
  - one `SystemMessage` first
  - followed by the original `state.messages` objects unchanged and in the
    same order
- The planner prompt contains:
  - `Existing profiles:`
  - `Existing messages:`
  - the existing profile id text such as `Obj_id = user_001`
  - a formatted human message line including its id

## What this test file should not try to cover

- real planner quality
- live LLM behavior
- full create/update classification scenarios
- downstream routing behavior

## Assumptions

- At this stage, one deterministic prompt-contract test is enough.
- Broader scenario coverage for planner semantics can be added later if the
  planner prompt becomes a frequent source of regressions.
