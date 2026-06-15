# Test Parent Subject Routing Integration V3 Microplan

## Scope

Create `tests/test_parent_subject_routing_integration_v3.py` for complete,
single-invocation execution of the compiled parent graph:

- `subject_planner_node(...)`
- create and update fanout
- branch wrappers and real compiled subgraphs
- reducer merge-back into final parent `existing`

Do not test checkpointed multi-turn behavior or interrupt-based repair here.

## Current Contract

One parent invocation receives a batch of messages and the current `existing`
profiles. The subject planner returns one bucket per detected person. The
router fans each new bucket into an extraction branch and each existing bucket
into an update branch.

Every branch receives only its selected subject/profile and supporting
messages. Each branch returns a partial `existing` slice. The parent reducer
must preserve every distinct-ID branch result regardless of parallel branch
completion order.

## Test Harness

- Compile a fresh parent graph for every test without a checkpointer.
- Replace `graphv3.llm` with one deterministic fake that selects outputs by
  requested schema and prompt content, never by concurrent call order.
- Use the real parent nodes, router, wrappers, extract subgraph, update
  subgraph, and `merge_profiles` reducer.
- Assert final state by profile IDs or profile values, never by branch
  completion order.
- Record fake-model prompts so branch message isolation can be asserted.

## Tests To Create

### 1. No Subjects Completes Without Branch Work

Return an empty `SubjectBucketList` for a low-signal message while an existing
profile is already present.

Assert:

- the compiled parent graph completes
- `existing` remains unchanged
- `subjects` is empty
- neither `UserProfile` extraction nor `PatchProposalList` update output is
  requested

### 2. Create-Only Batch Merges Several Distinct Profiles

Use several messages describing two new people. Include:

- one shared message mentioning both people
- one subject-specific message for each person
- one person repeated across several messages

Return two new subject buckets and subject-specific `UserProfile` outputs.

Assert:

- both created profiles survive final merge-back
- their generated profile IDs are distinct
- each extraction prompt contains the shared message and its own
  subject-specific evidence
- each extraction prompt excludes the other subject's specific evidence
- only create branches run

### 3. Update-Only Batch Merges A Real Update And A No-Op

Start with two existing profiles. Use a shared message mentioning both plus
subject-specific messages. Route one bucket to a real update and the other to
an empty `PatchProposalList`.

Assert:

- both original IDs survive final merge-back
- the actionable profile is updated
- the no-op profile remains unchanged
- each update prompt receives only shared evidence plus its own
  subject-specific evidence
- only update branches run

### 4. Mixed Batch Preserves Every Create And Update Result

Use one shared message mentioning several new and existing people, plus
subject-specific messages for each. Return at least two new and two existing
subject buckets. Produce create outputs for both new subjects, one real update,
and one no-op update.

Assert:

- all original and newly created profiles coexist in final `existing`
- all created IDs are distinct from each other and existing IDs
- the real update is committed and the no-op profile is preserved
- shared evidence reaches every relevant branch
- subject-specific evidence remains isolated to its branch
- create and update outputs all survive the same parent superstep

## Must Not Test Here

- direct fanout or wrapper contracts already covered by focused files
- checkpointed second turns, message accumulation, or thread isolation
- update repair retries or `human_repair`
- malformed or duplicate bucket defensive policy
- scheduler branch completion order

## Must Not Change

- production code
- existing tests
- parent graph architecture

## Run Command

```bash
.venv/bin/pytest -q tests/test_parent_subject_routing_integration_v3.py
```

## Approval Checkpoint

Approve this microplan before reviewing it or creating the test file.
