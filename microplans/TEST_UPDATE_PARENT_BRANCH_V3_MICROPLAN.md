# Test Update Parent Branch V3 Microplan

## Scope

Create `tests/test_update_parent_branch_v3.py` for the parent-to-update branch
boundary:

- routed update payload produced by `fan_out_updates(...)`
- `run_update_subgagent(...)`
- real compiled `update_subgraph` only where needed to prove routed execution

Do not repeat update-subgraph internal retry tests or parent parallel
merge-back tests.

## Current Contract

One existing `SubjectBucket` produces one `Send("update_subagent", ...)`
payload containing:

- exactly one selected existing profile
- only that subject's supporting messages

`run_update_subgagent(...)` receives that dictionary-shaped routed payload,
invokes `update_subgraph` with only `messages` and `existing`, and returns only
the committed `existing` slice as a partial parent-state update.

## Tests To Create

### 1. Wrapper Preserves Real Routed Payload And Returns Partial Update

Build a `MainState` with one existing subject supported by several messages.
Use real `fan_out_updates(...)` to obtain its `Send.arg`. Replace
`update_subgraph` with a capturing fake.

Assert:

- the wrapper invokes the subgraph exactly once
- the subgraph input contains only `messages` and `existing`
- exactly one selected existing profile is passed
- every routed supporting message is preserved
- the wrapper returns only `{"existing": ...}`, ignoring other subgraph state

This proves the wrapper contract without duplicating fanout filtering details.

### 2. Routed One-Message No-Op Completes Through Real Update Subgraph

Build a routed payload from one existing bucket and one supporting no-op
message. Use the real compiled `update_subgraph` and a deterministic fake LLM
that returns an empty `PatchProposalList`.

Assert:

- the routed dictionary payload completes without type or state-shape errors
- the fake LLM is called once
- the wrapper returns only the selected unchanged profile in `existing`
- the original profile value is preserved

This complements the internal no-op integration test by proving the real
parent wrapper accepts the runtime payload produced by `Send`.

### 3. Missing Required Routed State Fails Before Subgraph Invocation

Call `run_update_subgagent(...)` with:

- a dictionary payload missing `existing`
- a dictionary payload missing `messages`

Use a capturing fake subgraph.

Assert:

- each case raises `KeyError` naming the missing key
- the subgraph is not invoked

## Deterministic Boundaries

- Use real `MainState`, `SubjectBucket`, `UserProfile`, and `Send.arg` payloads.
- Use a capturing fake subgraph only for wrapper translation assertions.
- Use the real compiled update subgraph only for the routed no-op case.
- Replace `graphv3.llm` with a deterministic fake for the real no-op case.

## Must Not Test Here

- fanout filtering combinations already covered by `test_subject_fanout_v3.py`
- update-subgraph retry or human repair
- multiple update branches
- parent reducer merge-back
- parent graph routing

Those contracts belong to existing internal tests or later parent integration.

## Must Not Change

- production code
- existing tests
- update branch architecture

## Run Command

```bash
.venv/bin/pytest -q tests/test_update_parent_branch_v3.py
```

## Approval Checkpoint

Approve this microplan before reviewing it or creating the test file.

