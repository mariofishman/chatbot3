# Test Parallel Update Repair Integration V3 Microplan

## Scope

Create `tests/test_parallel_update_repair_integration_v3.py` for complete
parent-graph runs containing several parallel update branches when one branch
requires repair.

Cover:

- automatic model repair inside one parallel update branch
- parent-level interruption after one branch reaches `human_repair`
- simultaneous human-repair interruptions resolved one at a time
- durable successful-sibling state while interrupted
- resume and final merge-back of successful and repaired sibling branches

Do not repeat direct `patch(...)`, `human_repair(...)`, or update-subgraph unit
tests.

## Current Contract

The parent router may schedule several `update_subagent` branches in one
parallel superstep. Each branch owns exactly one existing profile and returns a
partial `existing` slice.

If one branch repairs itself with `patch(...)`, every successful branch result
must merge into final parent `existing`.

If one branch reaches `human_repair`, the parent run pauses. The parallel
superstep remains incomplete, but completed sibling-task writes are durable and
are exposed by `graph.get_state(config)`. The interrupted profile must remain
unchanged until the human repair is supplied.

Resume requires a checkpointer, the original thread ID, and a
`Command(resume={interrupt_id: value})` mapping.

If several branches reach `human_repair` together, each interrupt may be
resolved in a separate invocation. Each resume payload must be paired with its
LangGraph-generated interrupt ID. After each invocation, the returned
`__interrupt__` collection identifies only the branches that still need human
input.

## Test Harness

- Compile a fresh parent graph with a fresh `InMemorySaver` per test.
- Use real parent routing, wrappers, update subgraphs, validation, repair,
  interrupt, commit, and parent reducer behavior.
- Replace `graphv3.llm` with a thread-safe deterministic fake that routes
  `SubjectBucketList` and `PatchProposalList` outputs by schema, target profile
  ID, and whether the prompt is an initial update or repair prompt.
- Never rely on parallel branch invocation or completion order.
- Inspect `graph.get_state(config)` at the interrupt boundary.
- Resume using the actual interrupt ID returned by the paused run.

## Tests To Create

### 1. Parallel Successful And Model-Repaired Updates Both Commit

Start with two existing profiles and route one update branch per profile:

- one branch produces a valid patch immediately
- one branch first produces an invalid field type, then receives a valid
  corrective patch from `patch(...)`

Assert:

- the parent graph completes without interruption
- both original profile IDs survive
- both requested updates appear in final `existing`
- the repaired branch preserves its other valid fields
- the repaired branch used the repair prompt containing failed candidate and
  validation errors
- the immediately successful branch was not sent through model repair

### 2. Human Repair Preserves Completed Sibling And Resume Merges Repair

Start with two existing profiles and route one update branch per profile:

- one branch completes successfully
- one branch repeatedly returns an invalid field type until it reaches
  `human_repair`

Invoke the checkpointed parent graph and inspect its paused state.

Assert before resume:

- exactly one interrupt is pending and its payload identifies the failed target
- parent `existing` contains the successful sibling's completed update
- the interrupted profile still contains its original valid data

Resume with a valid corrective `PatchProposalList` payload mapped to the
actual interrupt ID.

Assert after resume:

- the graph completes with no pending interrupts
- the successful sibling update and human-repaired update both appear in final
  `existing`
- both original profile IDs survive
- the successful sibling branch is not recomputed after resume

### 3. Multiple Human Repairs Resume One At A Time By Interrupt ID

Start with three existing profiles and route one update branch per profile.
Make every branch repeatedly produce an invalid field type until all three
reach `human_repair`.

Assert before resume:

- exactly three interrupts are pending
- their payloads identify the three distinct failed targets
- all three profiles still contain their original valid data

Resolve one interrupt per invocation, using the same thread ID and a mapping
containing only that interrupt ID and its corrective `PatchProposalList`.

Assert after each resume:

- the repaired profile update becomes visible
- the returned `__interrupt__` collection contains only unresolved branches
- unresolved profiles remain unchanged

Assert after the final resume:

- the graph completes without `__interrupt__`
- all three repaired updates appear in final `existing`
- every original profile ID survives
- no branch returns to model repair after its human resume

## Must Not Test Here

- malformed human resume payload retry behavior
- create-branch failures
- duplicate update branches targeting the same profile
- checkpointed conversational turns after the repaired run

## Must Not Change

- production code
- existing tests
- parent or update-subgraph architecture

## Run Command

```bash
.venv/bin/pytest -q tests/test_parallel_update_repair_integration_v3.py
```

## Approval Checkpoint

Approve this microplan before reviewing it or creating the test file.
