# Suite Tests Microplan

This microplan defines the regression test suite for the current live codebase:

- `src/graphv3.py`
- `src/state.py`

The goal is to keep stable behavior protected as new features are added, so
future changes can be repaired against deterministic tests instead of relying
on memory or manual inspection.

## Index Of Test Files

### Existing current tests

- `tests/test_update_fanout_v3.py`
- `tests/test_apply_patch_v3.py`
- `tests/test_update_patches_v3.py`
- `tests/test_route_after_planner_v3.py`
- `tests/test_extract_subagent_v3.py`
- `tests/test_human_v3.py`
- `tests/test_helpers_v3.py`
- `tests/test_planner_node_v3.py`
- `tests/test_state_reducers_v3.py`

### Mapping note

The numbered targets below are not meant to map 1:1 to files.
Some files intentionally cover multiple closely related targets.

Examples:
- `tests/test_extract_subagent_v3.py` covers both the extract wrapper and the
  extract node
- `tests/test_update_fanout_v3.py` already covers both `fan_out_updates` and
  `run_update_subgagent`

## Scope

This suite should focus first on the parts that already exist and should be
kept stable:

- helpers
- create-side wrapper and node behavior
- update fan-out and update wrapper behavior
- `update_patches`
- `apply_patch`
- reducers

The nodes that are still unfinished (`validate`, `route_patches`, `patch`,
`commit`) should not drive the current suite yet. They can be added once they
exist.

## 1. Helper formatting functions

Planned file:
- `tests/test_helpers_v3.py`

What it should test:
- `annotation_to_text` formats plain, optional, and list annotations correctly
- `format_messages` includes human and ai messages and includes IDs
- `format_string_from_user_profile` returns stable field formatting
- `format_string_from_schema` includes field descriptions and types

How:
- call each helper directly with small fixtures
- assert deterministic string contents

## 2. `planner_node`

Planned file:
- `tests/test_planner_node_v3.py`

What it should test:
- node stores the structured planner result into `plan`
- prompt path can be exercised with a fake structured LLM
- one integration-style prompt test can later check create-only, update-only,
  mixed, and no-op scenarios if needed

How:
- mock the structured LLM output
- assert that the returned `plan` is exactly what the node stores into state

## 3. `run_extract_subgagent`

Planned file:
- `tests/test_extract_subagent_v3.py`

What it should test:
- filters only create-relevant messages
- passes narrowed create-side plan
- does not leak update-side links into the extract subgraph
- passes empty `existing` into the extract subgraph input

How:
- replace `extract_subgraph` with a fake
- capture the wrapper input passed into `invoke`
- assert filtered messages and narrowed plan fields

## 4. `extract_node`

Planned file:
- `tests/test_extract_subagent_v3.py`

What it should test:
- successful extraction when count matches
- retry path when first extraction count mismatches
- human handoff path when retry still mismatches
- successful output becomes `existing` with generated ids
- retry prompt uses the same filtered messages and expected count

How:
- mock structured LLM responses in sequence
- assert returned `Command.goto`
- assert update payload shape

## 5. `human`

Planned file:
- `tests/test_human_v3.py`

What it should test:
- valid `UserProfileList` payload is accepted
- invalid payload triggers retry interrupt flow
- validated payload becomes `existing`
- generated IDs are created for accepted human profiles

How:
- fake `interrupt(...)`
- feed one invalid payload and then one valid payload
- assert final `existing` output

## 6. `fan_out_updates`

Covered by existing file:
- `tests/test_update_fanout_v3.py`

What it should test:
- groups update links by `user_id`
- one user mentioned in multiple messages gets all relevant messages
- one `existing` profile per `Send`
- invalid/stale user ids are skipped
- each `Send` still carries the parent `plan` because the current wrapper
  depends on it

How:
- build a fake `MainState`
- call `fan_out_updates`
- inspect returned `Send` objects and payloads

## 7. `route_after_planner`

Planned file:
- `tests/test_route_after_planner_v3.py`

What it should test:
- create-only returns only `"extract_subagent"`
- update-only returns only `Send(...)`
- mixed case returns both
- no work returns `["__end__"]`
- `__end__` is not mixed with other destinations

How:
- build several `MainState.plan` scenarios
- assert the returned routing list shape

## 8. `run_update_subgagent`

Covered by existing file:
- `tests/test_update_fanout_v3.py`

What it should test:
- converts per-user parent payload into `UpdateAgentState` input
- passes one-user `messages`
- passes one-user `existing`
- extracts `reasoning_summary_for_update` correctly
- returns only the committed `existing` slice from the subgraph result

How:
- replace `update_subgraph` with a fake
- capture wrapper input to `invoke`
- assert the constructed sub-state

## 9. `update_patches`

Planned file:
- `tests/test_update_patches_v3.py`

What it should test:
- rejects zero or multiple target profiles in `existing`
- stores structured output into `patches`
- respects one-target architecture
- prompt includes supporting summary and existing profile context
- prompt path does not depend on `plan`

How:
- mock `llm.with_structured_output(...).invoke(...)`
- assert returned `patches`
- add one failure case for bad `existing` size

## 10. `apply_patch`

Covered by existing file:
- `tests/test_apply_patch_v3.py`

What it should test:
- add / replace / remove happy path
- invalid target id rejected
- empty `patches` rejected
- invalid path rejected
- remove missing key rejected
- list append with `/-`
- list index replacement such as `/interests/1`
- nested path such as `/company/address/city`
- root-path / malformed path is rejected
- unsupported patch op is rejected

How:
- use deterministic in-memory `UpdateAgentState`
- call `apply_patch(...)`
- assert `candidate` or raised exceptions

## 11. `merge_profiles`

Planned file:
- `tests/test_state_reducers_v3.py`

What it should test:
- adds brand-new ids
- replaces the whole profile when the same user id appears in both dicts
- keeps existing profiles whose ids are absent from `new`
- handles empty dict inputs and `None`
- returns a fresh dict without mutating the inputs

How:
- call reducer directly with small dict fixtures
- assert returned dict contents

## 12. Current integration smoke tests

Covered by existing files:
- `tests/test_update_fanout_v3.py`
- `tests/test_apply_patch_v3.py`

What it should test:
- `tests/test_update_fanout_v3.py` remains green
- `tests/test_apply_patch_v3.py` remains green

How:
- keep these as lightweight architecture smoke tests
- run them after each new node is added

## Current status

All currently planned test files in this suite now exist.

What remains for the future is not more test-file creation for the current
surface area, but extending the suite when these unfinished update nodes are
implemented:

- `validate`
- `route_patches`
- `patch`
- `commit`

## Completeness Check

For the code that exists today, the current plan is complete enough:

- the 12 numbered targets cover the live helpers, reducers, wrappers, and
  implemented nodes
- the 2 existing test files already cover the update fan-out architecture and
  `apply_patch()` smoke path
- the 7 planned new files are enough to cover the remaining built behavior

No additional test files are needed right now for the current codebase.
More files should only be added later when `validate`, `route_patches`,
`patch`, or `commit` are implemented.

## Deprecated Tests

These should not drive current regression decisions:
- `tests/DEPRECATEDtest_planner.py`
- `tests/DEPRECATEDtest_plannerv2.py`
- `tests/DEPRECATEDtest_plannerv3.py`

## General Rule

Prefer deterministic unit tests with mocks/fakes around LLM calls.

Prefer `pytest` style for all new tests:
- plain `assert`
- small fixtures/builders
- monkeypatch or fake objects for LLM/subgraph dependencies
- no dependence on live model output for regression checks

Why:
- future refactors should be repairable against stable regression tests
- failures should point to code regressions, not model randomness
