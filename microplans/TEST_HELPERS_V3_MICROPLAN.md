# Test Helpers V3 Microplan

Scope: create `tests/test_helpers_v3.py` only.

## Relevant inputs

- `microplans/SUITE_TESTS.md`, target `1. Helper formatting functions`
- `src/graphv3.py`, helpers:
  - `annotation_to_text`
  - `format_string_from_schema`
  - `format_messages`
  - `format_string_from_user_profile`
- `src/state.py`, models used by the helpers:
  - `UserProfile`

## What this test file should cover

1. `annotation_to_text(...)`
   - plain type formatting, such as `str`
   - optional formatting, such as `str | None`
   - list formatting, such as `list[str]`

2. `format_messages(...)`
   - includes only `human` and `ai` messages
   - includes message ids
   - excludes non-human/non-ai message types

3. `format_string_from_user_profile(...)`
   - returns stable `key : value` lines for a `UserProfile`

4. `format_string_from_schema(...)`
   - includes field descriptions
   - includes field type text generated through `annotation_to_text(...)`

## How the test should be built

- Use deterministic direct unit tests.
- Call the helpers directly with tiny fixtures.
- Avoid any LLM, graph, or subgraph setup.

## What the tests should assert

- `annotation_to_text(...)`
  - `str` becomes `"str"`
  - `str | None` becomes `"Optional[str]"`
  - `list[str]` becomes `"list[str]"`

- `format_messages(...)`
  - a mixed message list produces lines for `human` and `ai`
  - include at least one non-human/non-ai message fixture, such as `system`,
    and assert it is excluded
  - each kept line includes `type`, `content`, and `id`
  - a non-human/non-ai message is not present in the output

- `format_string_from_user_profile(...)`
  - output contains expected lines like `name : ...` and `location : ...`
  - list fields such as `interests` appear in the dumped output

- `format_string_from_schema(...)`
  - output contains representative field names from `UserProfile`
  - output contains field descriptions
  - output contains type text such as `str`, `Optional[str]`, and `list[str]`

## What this test file should not try to cover

- prompt wording
- planner behavior
- state reducers
- any graph execution

## Assumptions

- The helper outputs should be checked by stable string contents, not by full
  exact multiline equality unless needed.
- The current `annotation_to_text(...)` behavior for `str | None` should be
  treated as intentional and protected by this test.
