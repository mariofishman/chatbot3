# Test Extract Branch V3 Create-Recovery Extension Microplan

## Scope

Extend `tests/test_extract_branch_v3.py` for the create-recovery lifecycle now
implemented inside `extract_subgraph`:

- `extract_node(...)`
- `route_extraction(...)`
- `human_create_repair(...)`
- `route_after_human_create_repair(...)`
- `commit_created_profile(...)`
- compiled `extract_subgraph`
- `run_extract_subgagent(...)`

Preserve the original happy-path, sparse-profile, prompt, routed-payload, and
wrapper-contract coverage already in this file.

## Human Response Contract

Production now uses this explicit one-time human response envelope:

- submit a profile: `{"action": "submit", "profile": {...}}`
- decline creation: `{"action": "decline"}`

Unknown or missing actions, non-dictionary responses, and submit actions with
missing or invalid profiles end without creating a profile.

## Updated Contract

One new `SubjectBucket` and its supporting messages enter one extraction
branch.

- `extract_node(...)` returns a valid uncommitted `candidate`, or retries once
  and returns the latest extraction errors
- `route_extraction(...)` sends a valid candidate to commit and failed
  extraction to one human interrupt
- valid submitted human profile becomes the candidate and commits
- decline, missing/unknown actions, and invalid submitted profiles end the
  branch without another interrupt or created profile
- `commit_created_profile(...)` is the only node that generates a UUID and
  writes `existing`
- the wrapper continues returning only the committed partial parent
  `{"existing": ...}` update

## Test-Harness Changes

- Extend the fake structured LLM so scripted results may be values or raised
  expected extraction exceptions.
- Compile a fresh extract subgraph with `InMemorySaver` for interrupt/resume
  scenarios.
- Use unique thread IDs for each checkpointed test.
- Resume human repair with `Command(resume=...)`.
- Monkeypatch `graphv3.uuid.uuid4` where a test must prove that UUID generation
  happens only after commit.
- Do not assert exact generated UUID values.

## Existing Tests To Adapt

### Direct `extract_node(...)` Assertions

Update direct node tests so they assert:

- `candidate` contains the extracted `UserProfile`
- `errors` is empty
- no `existing` slice or generated UUID is returned by `extract_node(...)`

Keep prompt-content and subject-label assertions unchanged.

### Compiled Subgraph And Wrapper Assertions

Keep compiled happy-path assertions expecting one committed profile with a
valid generated UUID.

Keep wrapper assertions confirming that only `subject` and filtered `messages`
enter the subgraph and only committed `existing` returns to the parent.

## New Tests To Add

### 1. First Extraction Failure Retries Once And Commits

Parameterize recoverable first-attempt failures to include:

- missing structured output (`None`)
- empty or unknown-fields-only output that produces no meaningful profile data
- one structured-output parsing or `UserProfile` validation failure

Follow each failure with one valid `UserProfile`.

Assert:

- exactly two model calls occur
- the retry prompt contains the first failure and original task
- the compiled subgraph commits exactly one profile
- no interrupt occurs

### 2. Two Extraction Failures Produce One Human Interrupt

Script two recoverable failures and invoke a freshly checkpointed extract
subgraph.

Assert:

- exactly two model calls occur
- one interrupt is returned
- the interrupt payload contains the subject label, formatted supporting
  messages, latest extraction errors, and response examples for submitting or
  declining one `UserProfile`
- checkpointed state has no candidate and no committed profile

### 3. Valid Human Response Commits Once

Resume the interrupted branch with:

```python
{"action": "submit", "profile": valid_profile_data}
```

Assert:

- the branch commits exactly that profile under one valid generated UUID
- no additional model call or interrupt occurs
- UUID generation happens only after the human response is validated

### 4. Schema-Invalid Human Response Ends Without Creating

Resume the interrupted branch with `action="submit"` and a schema-invalid or
missing profile, and separately with an empty or unknown-fields-only profile.

Assert:

- execution ends without another interrupt
- no candidate or committed profile is produced
- validation errors remain available in extract-subgraph state

### 5. Declined Or Missing Human Response Ends Without Creating

Resume the interrupted branch with:

- `{"action": "decline"}`
- missing or unknown action
- a non-dictionary response

Assert:

- execution ends without another interrupt
- no candidate or committed profile is produced
- the branch does not generate a UUID

Confirm that `{}` does not accidentally validate and commit as an empty sparse
profile.

### 6. Commit Boundary Rejects Invalid State

Call `commit_created_profile(...)` directly with:

- no candidate
- non-empty errors
- pre-populated branch-local `existing`

Assert each invalid state fails clearly and no UUID-producing committed slice
is returned.

### 7. Unexpected Errors Still Propagate

Make the structured call raise one unexpected programming or infrastructure
exception.

Assert:

- the exception propagates immediately
- no model retry, interrupt, or commit occurs

### 8. Routing Functions Reject Contradictory State

Call `route_extraction(...)` and `route_after_human_create_repair(...)`
directly with relevant boundary state shapes:

- candidate and errors both present
- candidate and errors both absent after human repair

Assert:

- either router rejects candidate plus errors
- `route_extraction(...)` rejects candidate and errors both absent
- `route_after_human_create_repair(...)` routes candidate and errors both
  absent to `END`

## Must Not Test Here

- parallel create branches or parallel create interrupts
- parent create/update sibling preservation
- update-side retry or human repair
- duplicate subject buckets
- live-model semantic accuracy

Those integration behaviors belong to Test 10 or later workflows.

## Must Not Change

- production code
- create fanout payload shape
- wrapper input/output contract
- update-side behavior

## Run Command

```bash
.venv/bin/pytest -q tests/test_extract_branch_v3.py
```
