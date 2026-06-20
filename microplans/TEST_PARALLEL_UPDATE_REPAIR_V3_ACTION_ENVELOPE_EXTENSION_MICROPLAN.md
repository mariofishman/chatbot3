# Test Parallel Update Repair V3 Action-Envelope Extension Microplan

## Scope

Extend `tests/test_parallel_update_repair_integration_v3.py` for the new
update-side human repair envelope and decline behavior.

Preserve the existing parent-level guarantees:

- successful sibling updates survive while other branches are interrupted
- several parallel interrupts can be resumed one at a time by interrupt ID
- completed branch results are visible in checkpointed state

## Updated Contract

Each interrupted update branch now expects one of:

- `{"action": "submit", "patches": {"items": [...]}}`
- `{"action": "decline"}`

The old raw `{"items": [...]}` resume payload is stale.

Declined or invalid human responses must not interrupt again and must leave
that branch's original profile unchanged.

## Existing Tests To Adapt

Update valid human repair resumes so they use the submit envelope.

Keep the existing assertions that:

- repaired branches merge after resume
- completed siblings are not re-run
- unresolved interrupts remain addressable by interrupt ID

## New Tests To Add

### 1. One Declined Update Preserves Successful Sibling

Build a parent run with two update branches:

- one branch commits successfully before interruption
- one branch reaches human repair

Resume the human branch with `{"action": "decline"}`.

Assert:

- successful sibling update remains committed
- declined profile remains unchanged
- no second interrupt occurs

### 2. Mixed Submit And Decline Across Several Interrupts

Build three interrupted update branches.

Resume them one at a time by interrupt ID:

- one valid submit
- one decline
- one valid submit

Assert after each resume:

- completed submitted branch updates become visible
- declined branch remains unchanged
- unresolved branches remain listed in `__interrupt__`
- no declined branch interrupts again

## Must Not Test Here

- direct `human_repair(...)` malformed payload variants
- create-side interrupts
- duplicate subject bucket policy

Those belong to focused unit tests, Test 10, or Test 11.

## Run Command

```bash
.venv/bin/pytest -q tests/test_parallel_update_repair_integration_v3.py
```
