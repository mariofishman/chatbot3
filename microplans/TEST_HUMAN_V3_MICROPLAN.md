# Test Human V3 Microplan

Scope: create `tests/test_human_v3.py` only.

## Relevant inputs

- `microplans/SUITE_TESTS.md`, target `5. human`
- `src/graphv3.py`, function `human(state: ExtractAgentState)`
- `src/state.py`, models `ExtractAgentState`, `UserProfile`, `UserProfileList`

## What this test file should cover

1. Valid human payload is accepted on the first interrupt/resume cycle.
2. Invalid human payload triggers a second `interrupt(...)` call with:
   - a retry message
   - validation errors
   - an `expected_format`
3. After a valid payload is finally received, the function returns an
   `existing` dict with generated ids mapped to `UserProfile` values.

## How the test should be built

- Use deterministic tests.
- Monkeypatch `graphv3.interrupt` with a fake that returns controlled payloads:
  - one test with a valid payload immediately
  - one test with an invalid payload first, then a valid payload
- Monkeypatch `uuid.uuid4` so generated ids are stable and assertable.

## What the tests should assert

- First-pass valid case:
  - the first `interrupt(...)` input is exactly `state.human_prompt`
  - `human(...)` returns `{"existing": {...}}`
  - exactly one stable generated id is used
  - the stored profile fields match the valid payload

- Retry case:
  - `interrupt(...)` is called twice
  - the first interrupt input is exactly `state.human_prompt`
  - the second interrupt input is a dict containing:
    - `message`
    - `errors`
    - `expected_format`
  - final return still contains valid `existing` output

## What this test file should not try to cover

- `extract_node()` retry/handoff logic
- the surrounding extract subgraph wiring
- live LangGraph interrupt runtime behavior beyond the local function contract

## Assumptions

- Testing `human(...)` as a plain function with monkeypatched `interrupt` is
  enough for this stage.
- The exact validation error payload from Pydantic should be checked only
  structurally, not by full string equality.
