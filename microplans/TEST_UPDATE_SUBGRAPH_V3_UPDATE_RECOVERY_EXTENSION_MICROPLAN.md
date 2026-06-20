# Test Update Subgraph V3 Update-Recovery Extension Microplan

## Scope

Extend `tests/test_update_subgraph_integration_v3.py` for the new
one-interrupt update human-repair policy inside `update_subgraph`.

Preserve existing coverage for:

- model repair after a validation failure
- no-op updates from an empty `PatchProposalList`
- successful commit through `update_patches(...) -> apply_patch(...) ->
  validate(...) -> commit(...)`

## Updated Contract

The automated update loop is unchanged:

- invalid first patches produce a raw candidate
- `validate(...)` records model-repairable errors
- `patch(...)` retries up to the existing attempt limit
- valid repaired patches still commit

Only the human path after the retry limit changed:

- `human_repair(...)` interrupts once
- a valid submit envelope provides corrective patches:
  `{"action": "submit", "patches": {"items": [...]}}`
- a decline, malformed envelope, missing action, invalid patch list, empty
  patch list, or wrong target ends the branch without changing the profile
- no second human interrupt occurs

## New Tests To Add

### 1. Valid Human Submit Commits

Script model patch outputs that keep failing validation until the human path is
reached.

Resume the interrupt with a valid submit envelope.

Assert:

- the branch commits the corrected `UserProfile`
- submitted patches pass through `apply_patch(...)` and `validate(...)`
- no extra human interrupt occurs

### 2. Declined Human Repair Ends Unchanged

Reach the human interrupt and resume with:

```python
{"action": "decline"}
```

Assert:

- execution ends without another interrupt
- the result does not contain a changed committed profile
- checkpointed update state preserves a concise decline reason

### 3. Invalid Human Repair Ends Unchanged

Parameterize malformed human responses:

- non-dictionary response
- missing action
- unknown action
- submit with missing `patches`
- submit with empty `items`
- submit with a patch targeting another user id

Assert each case:

- routes to `END`
- does not call `apply_patch(...)` with stale automated patches
- does not commit a changed profile

## Must Not Test Here

- parent sibling preservation
- several parallel interrupts
- create-side recovery
- live-model behavior

Those belong to Test 9, Test 10, or later workflows.

## Run Command

```bash
.venv/bin/pytest -q tests/test_update_subgraph_integration_v3.py
```
