# Test Parent Multi-Turn Integration V3 Microplan

## Scope

Create `tests/test_parent_multiturn_integration_v3.py` for realistic repeated
invocations of the complete compiled parent graph with checkpointed state.

Cover behavior that cannot be proven by single-run parent integration:

- accumulated messages
- profiles created in one turn and selected for updates later
- replacement of prior `subjects`
- same-thread persistence and cross-thread isolation

Do not test interrupt/resume or parallel repair behavior here.

## Current Contract

Each invocation supplies only the new turn's messages. A checkpointer restores
the selected thread's prior `MainState`, and the `messages` reducer appends the
new messages once.

The next planner call sees accumulated messages and committed profiles. It may
classify a previously new person as existing by selecting the profile ID
created during an earlier turn. Later update branches must replace that same
profile instead of creating duplicates.

`subjects` has no accumulation reducer, so every planner result replaces the
prior turn's buckets. Under the current checkpoint-only architecture, different
thread IDs do not share messages, subjects, or profiles. Profile isolation is
temporary behavior, not the desired persistence contract; shared cross-thread
profiles are deferred to `src/SHORT_TERM_PLAN4.md`.

## Test Harness

- Compile a fresh parent graph with a fresh `InMemorySaver` for each test.
- Use unique thread IDs within and across tests.
- Invoke each turn with only its newly arrived `HumanMessage` objects, matching
  `playground_run_graph.py`.
- Replace `graphv3.llm` with a deterministic prompt-routing fake.
- Route extraction and update responses by schema and prompt markers, never by
  parallel branch call order.
- Derive later existing-subject IDs from the planner prompt's checkpointed
  existing-profile section. Do not hard-code UUIDs generated during earlier
  extraction branches.
- Inspect `graph.get_state(config)` after turns where checkpointed state shape
  is part of the contract.

## Tests To Create

### 1. Sparse Create, Enrichment, And Correction Reuse One Profile

Run three turns in one thread:

1. create a sparse Lucia profile
2. add Lucia's role and location
3. correct Lucia's location

The fake planner should classify Lucia as new only on the first turn and
select her committed generated ID on later turns.

Assert:

- exactly one profile exists after every turn
- the same generated profile ID survives all turns
- enrichment preserves prior fields
- correction replaces the targeted field without creating a duplicate
- checkpointed messages contain all three IDs exactly once and in arrival
  order

### 2. Several Created Profiles Followed By One Selected Update

First create two profiles in parallel. On the next turn, update only one of
them.

Assert:

- the planner selects the updated person's committed generated ID
- both profiles remain in final `existing`
- only the selected profile changes
- the untouched profile and its ID remain unchanged
- no extra profile is created

### 3. No-Subject Later Turn Clears Buckets But Preserves State

First create one profile. Then invoke the same thread with a message that
produces an empty `SubjectBucketList`.

Assert:

- the later planner output replaces the earlier subject bucket with an empty
  list
- no extraction or update branch runs on the second turn
- the committed profile remains unchanged
- both messages exist once in checkpointed state

### 4. Same Thread Accumulates While Different Threads Stay Isolated

Use one fresh checkpointed parent graph with two thread IDs:

- run two turns in thread A
- run one independent turn in thread B

Assert:

- thread A's second planner call sees both A messages and A's existing profile
- thread B's planner call sees only B's message and no A profile
- each thread's snapshot contains only its own messages, subjects, and
  profiles

This test documents current checkpoint behavior only. It must not be treated as
the intended cross-thread profile persistence design.

## Must Not Test Here

- single-run fanout, wrapper, or parallel merge-back contracts already covered
  by focused files
- live model quality
- interrupt/resume or `human_repair`
- duplicate same-ID sibling branches
- malformed planner identifiers

## Must Not Change

- production code
- existing tests
- checkpoint or parent graph architecture

## Run Command

```bash
.venv/bin/pytest -q tests/test_parent_multiturn_integration_v3.py
```

## Approval Checkpoint

Approve this microplan before reviewing it or creating the test file.
