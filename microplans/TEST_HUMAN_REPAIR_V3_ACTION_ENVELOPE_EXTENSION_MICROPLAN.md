# Test Human Repair V3 Action-Envelope Extension Microplan

## Scope

Rewrite `tests/test_human_repair_v3.py` around the new update-side
`human_repair(...)` contract.

This is the focused unit-level file for update human repair. It should test
`human_repair(...)`, `route_after_human_repair(...)`, and the existing
`route_patches(...)` handoff into human repair.

## Updated Contract

`human_repair(...)` no longer accepts a raw `PatchProposalList` and no longer
loops with repeated interrupts.

It interrupts once and expects exactly one action envelope:

- submit patches:
  `{"action": "submit", "patches": {"items": [...]}}`
- decline update: `{"action": "decline"}`

Valid submitted patches clear errors and route to `apply_patch(...)`.

Declined, malformed, missing-action, unknown-action, invalid, empty, or
wrong-target responses return no patches and route to `END`.

## Existing Tests To Replace

Remove expectations that:

- the interrupt payload uses raw `PatchProposalList` shape
- invalid human payloads cause another interrupt
- wrong-target human payloads cause another interrupt

Those are stale after the one-interrupt UX decision.

## New Tests To Add

### 1. Route Patches Still Enters Human Repair At Attempt Limit

Keep the existing route test.

Assert that `route_patches(...)` still returns `"human_repair"` when
validation errors remain and attempts have reached the limit.

### 2. Submit Envelope Returns Corrective Patches

Monkeypatch `graphv3.interrupt(...)` to return:

```python
{"action": "submit", "patches": {"items": [...]}}
```

Assert:

- one interrupt call occurs
- the interrupt payload contains `response_instruction` and
  `response_examples`
- returned patches equal the submitted proposals
- errors are cleared
- attempts are preserved
- `route_after_human_repair(...)` returns `"apply_patch"`

### 3. Decline Ends Without Patches

Return `{"action": "decline"}`.

Assert:

- patches are empty
- errors contain a concise decline reason
- `route_after_human_repair(...)` returns `"__end__"`
- no second interrupt occurs

### 4. Malformed Human Responses End Without Patches

Parameterize:

- non-dictionary response
- empty dictionary
- unknown action
- submit without `patches`
- submit with empty `items`
- submit with wrong target id

Assert:

- one interrupt call occurs
- patches are empty
- errors explain the failure
- post-human router returns `"__end__"`

### 5. Invalid Precondition States Still Fail Clearly

Keep or add direct precondition tests for:

- empty errors
- no existing target
- no candidate
- candidate id mismatch

## Run Command

```bash
.venv/bin/pytest -q tests/test_human_repair_v3.py
```
