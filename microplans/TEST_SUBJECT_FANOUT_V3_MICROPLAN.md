# Test Subject Fanout V3 Microplan

## Scope

Create `tests/test_subject_fanout_v3.py` for:

- `fan_out_creates(...)`
- `fan_out_updates(...)`
- `route_after_subject_planner(...)`

Test direct deterministic routing and `Send` payload construction only. Do not
invoke create or update subgraphs.

## Input

Build real `MainState` instances containing:

- ordered parent messages with stable IDs
- existing profiles when existing-subject buckets are used
- a `SubjectBucketList` containing new, existing, or mixed buckets

Inspect returned `Send.node` and `Send.arg` values directly.

## Tests To Create

### 1. No Subjects Route To End

Assert:

- `fan_out_creates(...)` returns no sends
- `fan_out_updates(...)` returns no sends
- `route_after_subject_planner(...)` returns only `["__end__"]`

### 2. Single New Subject Produces One Create Branch

Use one new bucket supported by several messages.

Assert:

- exactly one `Send("extract_subagent", ...)` is produced
- the router returns that same single create send
- its payload contains the exact bucket
- it contains all and only the bucket's supporting messages
- it does not contain parent `existing`

### 3. Single Existing Subject Produces One Update Branch

Assert:

- exactly one `Send("update_subagent", ...)` is produced
- the router returns that same single update send
- its payload contains exactly the selected existing profile
- it contains all and only the bucket's supporting messages
- it does not contain the subject bucket

### 4. Several New Subjects Produce One Branch Each

Assert:

- one create send is produced per new bucket
- each send carries its own subject bucket and filtered messages
- existing buckets do not enter create fanout

### 5. Several Existing Subjects Produce One Branch Each

Assert:

- one update send is produced per existing bucket
- each send contains only its selected profile and filtered messages
- new buckets do not enter update fanout

### 6. Mixed Routing Preserves Shared And Subject-Specific Evidence

Use one ordered parent-message list containing:

- one message shared by a new and existing subject
- one new-subject-specific message
- one existing-subject-specific message
- one unrelated message

Assert:

- the router returns both create and update sends and never `__end__`
- each branch receives the shared message
- each branch receives only its own subject-specific message
- neither branch receives the unrelated message
- branch messages follow parent-state order even when bucket `message_ids` are
  listed in another order

This combined case covers mixed routing, shared evidence, subject isolation,
unrelated exclusion, and parent-order preservation.

## Assertion Rules

- Compare sends by their `node` and `arg`; do not rely on object identity.
- Preserve bucket order only when asserting one branch per input bucket.
- Assert exact message-ID lists for every payload.
- Use real `SubjectBucket`, `SubjectBucketList`, and `UserProfile` objects.

## Must Not Test Here

- wrapper or subgraph execution
- parent graph integration
- unknown supporting-message IDs
- repeated message IDs
- missing existing candidate IDs
- duplicate semantic buckets

Those defensive or runtime contracts belong to later files.

## Must Not Change

- production code
- existing tests
- routing or fanout policies

## Run Command

```bash
.venv/bin/pytest -q tests/test_subject_fanout_v3.py
```

## Approval Checkpoint

Approve this microplan before reviewing it or creating the test file.
