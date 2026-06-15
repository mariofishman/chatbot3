# Test Extract Branch V3 Microplan

## Scope

Create `tests/test_extract_branch_v3.py` for the current one-subject create
branch:

- `extract_node(...)`
- compiled `extract_subgraph`
- `run_extract_subgagent(...)`

Do not recreate the removed batch-extraction retry or human-repair
architecture.

## Current Contract

One new `SubjectBucket` and its supporting messages enter one extraction
branch. `extract_node(...)` asks for exactly one `UserProfile`, assigns it a
generated ID, and returns an `existing` slice. The wrapper invokes the
compiled extract subgraph and returns only that `existing` slice as a partial
parent-state update.

## Deterministic Boundaries

- Replace `graphv3.llm` with a fake structured LLM for node and compiled
  subgraph tests.
- Replace `graphv3.extract_subgraph` with a capturing fake only when isolating
  the wrapper input/output contract.
- Use a real payload produced by `fan_out_creates(...)` for the routed-wrapper
  test.
- Do not assert the generated UUID's exact value; assert it is one valid,
  non-empty ID mapped to the expected profile.

## Tests To Create

### 1. Compiled Subgraph Creates One Named Profile

Invoke the real compiled `extract_subgraph` with one named subject and one
supporting message. Return a complete fake `UserProfile`.

Assert:

- the fake structured LLM uses the `UserProfile` schema
- exactly one model call occurs
- exactly one generated ID maps to the fake profile

### 2. Compiled Subgraph Accepts Sparse Valid Profile

Return a `UserProfile` containing only explicitly known information.

Assert:

- exactly one profile is returned
- unknown optional fields remain `None`
- unknown list information remains empty

This proves composition accepts sparse valid output, not that a live model
will always extract it correctly.

### 3. Unnamed Relationship Label Constrains Extraction

Use a bucket labeled `"John's friend"` and a supporting message that also
mentions John. Return a sparse profile with no invented name.

Assert:

- the prompt identifies `"John's friend"` as the extraction target
- the prompt includes the shared supporting message once
- the returned profile's name remains `None`

### 4. Several Supporting Messages Reach The Prompt Once Each

Invoke `extract_node(...)` with one subject and several supporting messages.

Assert:

- every supporting message ID and content appears once in the prompt
- the subject label appears in the prompt
- exactly one model call occurs

### 5. Wrapper Uses Real Routed Payload And Returns Partial Parent Update

Use `fan_out_creates(...)` to produce one real `Send.arg` payload. Pass that
payload to `run_extract_subgagent(...)` while replacing `extract_subgraph`
with a capturing fake.

Assert:

- the wrapper invokes the subgraph with only `subject` and `messages`
- the exact routed subject and filtered messages are preserved
- the wrapper returns only `{"existing": ...}`

### 6. Missing Required Routed State Fails Clearly

Call `run_extract_subgagent(...)` with a dictionary payload missing `subject`,
and separately with one missing `messages`.

Assert that each call raises `KeyError` naming the missing key and that the
capturing subgraph is not invoked.

This documents the wrapper boundary without defining policy for invalid
subject identifiers or message IDs.

## Must Not Test Here

- fanout filtering details already covered by `test_subject_fanout_v3.py`
- several parallel extraction branches or generated-ID uniqueness across them
- parent reducer merge-back
- live-model semantic accuracy
- create-side retry or human repair

## Must Not Change

- production code
- existing tests
- create-side architecture

## Run Command

```bash
.venv/bin/pytest -q tests/test_extract_branch_v3.py
```

## Approval Checkpoint

Approve this microplan before reviewing it or creating the test file.
