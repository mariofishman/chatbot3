# Test State Reducers V3 Extension Microplan

## Scope

Extend `tests/test_state_reducers_v3.py` with the branch-slice merge cases
assigned by `PART3_TEST_MACROPLAN.md`.

Keep this file focused on direct, deterministic `merge_profiles(...)` reducer
semantics. Do not test parent routing or LangGraph parallel execution here.

## Reducer Contract

`merge_profiles(existing, new)` returns a fresh dictionary that:

- preserves IDs absent from `new`
- adds IDs present only in `new`
- replaces the whole `UserProfile` for IDs present in both inputs

It does not merge fields within a profile.

## Tests To Add

### 1. Several Create Branch Slices Accumulate

Start from an existing profile dictionary, then apply two separate create
branch slices through consecutive `merge_profiles(...)` calls.

Assert:

- both newly created IDs survive
- the original profile survives unchanged
- no input slice is mutated

This models the reducer receiving separate new-profile results without testing
the parent graph itself.

### 2. Mixed Create And Update Slices Are Order-Independent For Distinct IDs

Prepare:

- one existing profile that will be replaced by a complete updated profile
- one create slice containing a different new ID
- one update slice containing the existing ID

Apply the create and update slices in both possible orders.

Assert:

- both orders produce the same final dictionary
- the new profile is present
- the updated profile fully replaces the old profile
- unrelated profiles remain unchanged

This proves order-independence only when branch slices modify distinct IDs.

### 3. Same-ID Slices Use Last-Write Whole-Profile Replacement

Prepare two complete branch slices containing different `UserProfile` objects
for the same ID.

Apply them in both possible orders.

Assert:

- the profile from the final applied slice is the final value
- reversing slice order reverses the final value
- fields are not combined across the two profiles

This documents the reducer's current same-ID collision behavior. It does not
claim that duplicate branches targeting one profile are desirable.

## Must Not Test Here

- whether fanout creates the correct branch slices
- whether LangGraph controls branch completion order
- parent graph parallel merge-back
- field-level profile merging
- duplicate-subject prevention policy

Those behaviors belong to later first-wave or deferred tests.

## Must Not Change

- production reducer code
- existing reducer tests
- parent graph or subgraphs

## Run Command

```bash
.venv/bin/pytest -q tests/test_state_reducers_v3.py
```

## Approval Checkpoint

Approve this extension microplan before reviewing it or changing the test file.

