# Test Upstream Subject Node V3 Extension Microplan

## Scope

Extend `tests/test_upstream_subject_node_v3.py` with the two checkpointed-state
cases assigned by `PART3_TEST_MACROPLAN.md`.

Do not repeat the existing direct-node, prompt, identifier-validation, retry,
or accumulated-message tests.

## Target Contract

`subject_planner_node(...)` returns a partial `MainState` update:

```python
{"subjects": SubjectBucketList(...)}
```

Because `MainState.subjects` has no reducer, each checkpointed invocation must
replace the previous `SubjectBucketList`. Because `MainState.messages` uses
`operator.add`, later invocations append the supplied message list to the
checkpointed messages. These controlled tests supply each message only once
and verify that the resulting history contains each one once.

## Test Graph

For each test, compile a fresh minimal graph containing only:

```text
START -> subject_planner_node -> END
```

Use:

- a fresh `InMemorySaver`
- a unique thread ID
- deterministic structured-output results in invocation order

The fake outputs test state-update behavior. They do not prove how a live model
will classify accumulated history.

## Tests To Add

### 1. Later Planner Output Replaces Earlier Subjects

Invoke the checkpointed graph twice on one thread:

1. A first message about Lucia produces a new-subject bucket for Lucia using
   the first message ID.
2. A second message about John produces a different new-subject bucket for
   John using the second message ID.

Assert:

- the final checkpoint contains only John's second subject output
- Lucia's first bucket does not remain merely because it existed earlier
- messages from both invocations remain present exactly once

This proves that `subjects` uses last-value replacement rather than
accumulation.

### 2. Empty Later Output Clears Earlier Subjects Safely

Invoke a separate fresh checkpointed graph twice:

1. A subject-bearing first message produces a non-empty subject output.
2. A later no-subject message is added and the deterministic planner output is
   an empty `SubjectBucketList`.

Assert:

- the final checkpoint contains an empty `subjects.items`
- the earlier and later messages remain present exactly once
- the second prompt receives the accumulated human-message history
- no exception occurs

This proves that an empty partial-state update can clear stale routing buckets.
It does not claim that a live model must return no subjects when earlier
subject-bearing messages remain in accumulated history.

## Must Not Test Here

- downstream routing after the empty subject output
- create or update fanout
- live-model semantic accuracy
- duplicate semantic buckets
- defensive behavior for unknown IDs

Those contracts belong to other first-wave or deferred test files.

## Must Not Change

- production code
- existing tests
- message or subject state reducers

## Run Command

```bash
.venv/bin/pytest -q tests/test_upstream_subject_node_v3.py
```

## Approval Checkpoint

Approve this extension microplan before reviewing it or changing the test file.
