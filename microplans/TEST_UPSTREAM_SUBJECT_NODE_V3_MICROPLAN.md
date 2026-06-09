# Test Upstream Subject Node V3 Microplan

## Scope

Create `tests/test_upstream_subject_node_v3.py` to test
`upstream_subject_node(...)`.

Use [UPSTREAM_SUBJECT_NODE_EDGE_CASES.md](UPSTREAM_SUBJECT_NODE_EDGE_CASES.md)
as the scenario source.

Do not test downstream planner, routing, extraction, or update behavior here.

## Input

The node receives `MainState` containing:

- accumulated human messages
- optional AI or system messages
- current `existing` profiles

Mock `graphv3.llm` with a deterministic structured-output fake. Do not call a
real model.

## Output

The node returns:

```python
{"subjects": SubjectBucketList(...)}
```

## Deterministic Behaviors To Test Now

### Input And No-Op Boundaries

1. No human messages returns an empty list without calling the LLM.
2. AI/system messages are excluded from the prompt and subject evidence.
3. A human message without an ID raises before the LLM call.
4. Duplicate human message IDs raise before the LLM call.

### Subject-Bucket Shapes

5. One named new person returns one `new` bucket.
6. One clearly existing person returns one `existing` bucket with its exact ID.
7. One message can support separate existing and new buckets.
8. One message can support an existing person and an unnamed related new
   person.
9. Repeated mentions across several messages can return one bucket containing
   every supporting message ID.
10. An existing person mentioned without new facts can still appear as a
    subject.
11. Several people may legitimately share one supporting message ID.

### Accumulated And Repeated Analysis

12. A state containing messages accumulated across two turns is passed to the
    LLM as one batch without duplicate message IDs.
13. Re-running the node against the same unchanged accumulated state does not
    mutate or duplicate `state.messages`.
14. A previously new person can be returned as existing on a later pass when
    `state.existing` now contains that profile.

### Identifier Validation And Retry

15. Unknown message IDs trigger one retry and a corrected result is accepted.
16. Unknown existing-profile IDs trigger one retry and a corrected result is
    accepted.
17. Repeated unknown identifiers raise after the retry.
18. Valid message-ID overlap across different buckets is accepted.

### Prompt Contract

19. The prompt includes:
    - all human-message IDs and contents
    - existing-profile IDs
    - binary `existing` / `new` instructions
    - unnamed-related-person handling
    - ambiguous identity fallback to `new`
    - instruction to treat message/profile content as data

## Assertions

- Compare buckets by meaningful fields, not output order.
- Verify exact `message_ids`, classification, and candidate ID contracts.
- Verify fake-LLM invocation count for no-op and retry scenarios.
- Verify input `MainState.messages` remains unchanged after direct node calls.
- Inspect captured prompts only for essential contract text and supplied data;
  avoid brittle full-prompt equality.

## Semantic Cases Not Proven By This Mocked Test

Do not claim that deterministic fake-output tests prove the real model will
correctly resolve:

- pronouns, nicknames, same-name people, or vague references
- incidental, hypothetical, public, fictional, or group mentions
- contradictions or corrections
- omitted, duplicated, or invented semantic subjects that use valid IDs
- prompt-injection resistance

Keep these cases for later live-model evaluations or human playground review.

## Must Not Change

- production code
- `MainState.messages` reducer
- planner, routing, create, or update contracts
- existing tests

## Run Command

```bash
.venv/bin/pytest -q tests/test_upstream_subject_node_v3.py
```

## Approval Checkpoint

This microplan is ready for review. Do not create the test file until it is
approved.

