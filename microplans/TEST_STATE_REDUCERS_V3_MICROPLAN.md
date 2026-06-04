# Test State Reducers V3 Microplan

Scope: create `tests/test_state_reducers_v3.py` only.

## Relevant inputs

- `microplans/SUITE_TESTS.md`, deferred target `11. merge_profiles`
- `microplans/MERGE_PROFILES_MICROPLAN.md`
- `src/state.py`, function `merge_profiles(...)`
- `src/state.py`, model `UserProfile`

## What this test file should cover

1. `merge_profiles(...)` adds a brand-new `user_id` from `new`.
2. `merge_profiles(...)` keeps existing profiles whose ids are absent from
   `new`.
3. `merge_profiles(...)` replaces the whole `UserProfile` when the same
   `user_id` exists in both dicts.
4. `merge_profiles(...)` safely handles empty dicts and `None`.
5. `merge_profiles(...)` returns a fresh dict and does not mutate the input
   dicts.

## How the test should be built

- Use deterministic direct unit tests.
- Call `merge_profiles(...)` directly with tiny dict fixtures.
- Use real `UserProfile` instances.
- Keep the tests focused on dict-level whole-profile overlay behavior only.

## What the tests should assert

- New-id case:
  - original ids remain present
  - the new id is added

- Missing-from-new case:
  - profiles present only in `existing` remain unchanged

- Shared-id case:
  - the profile for the shared id is exactly the one from `new`
  - this is whole-profile replacement, not field-level merging

- Empty and `None` handling:
  - `{}` merged with `{}` returns `{}`
  - `merge_profiles(None, new)` behaves like merging from an empty dict
  - `merge_profiles(existing, None)` behaves like merging with an empty dict

- Fresh-dict behavior:
  - the returned dict is a new dict object
  - the input dicts are not mutated

## What this test file should not try to cover

- field-level merging inside `UserProfile`
- reducer behavior through LangGraph runtime
- any update-subgraph logic

## Assumptions

- The approved reducer contract is dict-level whole-profile overlay by
  `user_id`.
- If the architecture later changes back toward partial-profile reducer logic,
  this test file should be revised rather than stretched.
