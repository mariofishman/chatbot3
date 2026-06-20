# Test Create Failure Policy V3 Microplan

## Scope

Create `tests/test_create_failure_policy_v3.py` for parent-level create failure
and recovery behavior after the create-recovery refactor.

This file should test integration behavior that is broader than
`tests/test_extract_branch_v3.py`.

## Production Contract

Each new subject enters one extract branch.

Inside that branch:

- first extraction succeeds, or
- first expected extraction failure retries once, or
- two expected extraction failures produce one human interrupt, or
- an invalid or declined human response ends the branch without creating a
  profile

Only `commit_created_profile(...)` generates a UUID and returns a committed
profile slice.

Parent `existing` must never expose uncommitted extract-local `candidate`
values.

## Test Harness

- Compile a parent graph with `InMemorySaver` for interrupt/resume scenarios.
- Use deterministic fake structured outputs keyed by schema and prompt content.
- Script `UserProfile` extraction failures with recoverable exceptions,
  `None`, or unusable empty profiles.
- Resume interrupts with `Command(resume={interrupt_id: payload})`.
- Use unique thread IDs per checkpointed scenario.

## Required Tests

### 1. First Extraction Succeeds Without Retry Or Interrupt

One new subject returns one valid `UserProfile`.

Assert:

- one `UserProfile` model call occurs
- no interrupt occurs
- one committed profile appears in parent `existing`

### 2. First Extraction Fails And Retry Succeeds

First model call returns a recoverable failure. Second call returns a valid
profile.

Assert:

- two `UserProfile` calls occur
- retry prompt includes the first error and original task
- one profile commits
- no interrupt occurs

### 3. Two Extraction Failures Produce One Interrupt

Both model attempts fail.

Assert:

- one interrupt is returned
- parent state does not expose an uncommitted profile
- interrupt payload includes subject label, supporting messages, latest error,
  and submit/decline response examples

### 4. Valid Human Submit Commits

Resume an interrupted create branch with:

```python
{"action": "submit", "profile": {...}}
```

Assert:

- one profile commits
- no further interrupt occurs
- UUID generation happens only after the valid human profile

### 5. Invalid Or Declined Human Response Ends Without Creating

Parameterize:

- `{"action": "decline"}`
- missing action
- unknown action
- non-dictionary response
- submit with missing profile
- submit with invalid or empty profile

Assert:

- execution ends without another interrupt
- no committed profile is returned for that branch
- parent `existing` does not contain an empty or partial failed profile

### 6. Successful Siblings Are Preserved While Create Branch Is Interrupted

Run a mixed parent scenario with:

- one successful create branch
- one successful update branch
- one create branch that reaches human repair

Assert:

- completed sibling work is visible in checkpointed state
- interrupted branch has no committed profile
- after valid human resume, all siblings merge into parent `existing`

### 7. Several Create Interrupts Resume One At A Time

Run several create branches that all reach human repair.

Resume them one at a time by interrupt ID with mixed submit and decline
responses.

Assert:

- submitted branches commit
- declined branches do not commit
- unresolved interrupts remain listed until answered
- no declined or invalid branch interrupts again

## Must Not Test Here

- direct `extract_node(...)` unit details already covered by
  `tests/test_extract_branch_v3.py`
- update-side malformed human repair variants already covered by
  `tests/test_human_repair_v3.py`
- duplicate subject bucket policy, which belongs to Test 11
- live LLM behavior

## Run Command

```bash
.venv/bin/pytest -q tests/test_create_failure_policy_v3.py
```
