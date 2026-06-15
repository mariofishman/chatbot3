# Test Update Subgraph No-Op Extension Microplan

## Scope

Extend `tests/test_update_subgraph_integration_v3.py` with the no-op update
case assigned by `PART3_TEST_MACROPLAN.md`.

Use the real compiled `update_subgraph`. Do not call its nodes manually.

## Input

Invoke the subgraph with one valid `UpdateAgentState` containing:

- exactly one existing profile
- one supporting message that mentions the profile without adding or changing
  any profile facts

Replace `graphv3.llm` with a deterministic fake structured LLM that returns one
empty `PatchProposalList`.

## Expected Graph Path

The compiled subgraph must compose the no-op path:

```text
update_patches -> apply_patch -> validate -> commit
```

The empty proposal list must not route through model repair or human repair.

## Assertions

Assert:

- the fake LLM is called exactly once for `PatchProposalList`
- the final committed `existing` slice contains exactly the original target ID
- the committed `UserProfile` equals the original complete profile
- `candidate` contains the unchanged raw profile data
- `errors` is empty
- `attempts` remains `0`
- no repair prompt is requested

These assertions prove that an empty model proposal safely composes through
the real update subgraph as an unchanged committed profile.

## Must Not Test Here

- whether a live model correctly recognizes a no-op message
- the parent update wrapper
- parallel parent merge-back
- repair or human-interrupt behavior
- individual-node error boundaries already covered by unit tests

## Must Not Change

- production code
- the existing retry-and-commit integration test
- other test files

## Run Command

```bash
.venv/bin/pytest -q tests/test_update_subgraph_integration_v3.py
```

## Approval Checkpoint

Approve this extension microplan before reviewing it or changing the test file.

