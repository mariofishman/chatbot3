# SHORT_TERM_PLAN3v4

This file is the executable roadmap for completing Part 3 of the project.

It preserves the work completed in Steps 1–3 of
[SHORT_TERM_PLAN3v3.md](/Users/mariofishman/projects/chatbot3/src/SHORT_TERM_PLAN3v3.md)
and replaces the remaining roadmap after a new architectural conclusion:

`SubjectBucketList` already contains the parent graph's complete routing plan.
The old `planner_node(...)` and its output schemas duplicate that information
and should be removed after their consumers have migrated.

For the broader architectural direction, see
[ARCHITECTURAL_NOTE.md](/Users/mariofishman/projects/chatbot3/ARCHITECTURAL_NOTE.md).

Where that older note recommends preserving `planner_node(...)`, `UpdateLink`,
or `MessageSelectionOutput`, this executable roadmap supersedes it. The later
discussion established that `SubjectBucketList` already contains the routing
information those structures duplicate.

## Part 3 Goal

Make one identified subject the unit of parent-graph work.

Each `SubjectBucket` must:

- represent exactly one detected person
- contain every supporting human-message ID for that person
- classify that person as `existing` or `new`
- contain the matched existing profile ID only when classified as `existing`

The parent graph must route directly from these buckets:

- one existing bucket -> one update branch
- one new bucket -> one create branch

## Scope Boundary

Part 3 includes:

- subject detection across a received message batch
- candidate retrieval from `state.existing`
- binary `existing` or `new` classification
- subject-bucket-based create and update fanout
- adaptation of both parent wrappers and both subgraph inputs
- removal of the redundant old planner architecture

Part 3 does not include:

- ambiguity or identity-clarification branches
- full identity resolution
- non-simple fact taxonomy
- linked-entity or relational-memory workflows

## Do Not Break

- one subject may be supported by several messages
- one message may support several subjects
- each update branch receives exactly one existing profile
- each create branch receives exactly one new subject
- update branches may produce no patches without failing
- update validation, repair, human interrupt, and commit behavior remain intact
- committed create and update results merge into parent `existing`
- the terminal runner continues submitting only new messages while checkpointed
  state supplies accumulated history

## Migration Rule

Do not delete old planner schemas while active functions still consume them.

For each path:

1. migrate the fanout helper
2. migrate its wrapper and subgraph input
3. migrate parent routing
4. only then remove obsolete planner fields and schemas

This keeps the graph usable during the refactor.

## Completed Steps

### Step 1: Define The New Upstream Schema

Completed:

- added `SubjectBucket`
- added `SubjectBucketList`
- defined one bucket as one person
- enforced:
  - `existing` requires `candidate_existing_id`
  - `new` requires `candidate_existing_id=None`

### Step 2: Extend Parent State

Completed:

- added `MainState.subjects`
- gave it an empty default
- preserved `existing` and its reducer
- left update-side state and reducer behavior unchanged

### Step 3: Add The Upstream Subject Node

Completed:

- added `upstream_subject_node(...)`
- temporarily wired `START -> upstream_subject_node -> planner`
- grouped repeated mentions of the same person
- classified subjects as `existing` or `new`
- included existing subjects even when no actionable update was detected yet
- supported named and unnamed new subjects
- validated returned message and existing-profile IDs
- retried once when the model returned unknown IDs
- documented and tested relevant edge cases

Current temporary architecture:

```text
START -> upstream_subject_node -> planner_node -> route_after_planner
```

The new node produces `state.subjects`, but the old planner and downstream
functions still consume `state.plan`.

## New Architectural Conclusion

`SubjectBucketList` makes these old planning structures redundant:

- `CreateLink`
- `UpdateLink`
- `MessageSelectionOutput`
- `MainState.plan`
- `reasoning_summary_for_create`
- `reasoning_summary_for_update`
- `planner_node(...)`

The subject node already:

- identifies each person
- groups that person's supporting messages
- decides whether the person is new or existing
- identifies the exact existing profile when applicable

Therefore:

- rename `upstream_subject_node(...)` to `subject_planner_node(...)`
- route directly from `state.subjects`
- do not create another intermediate planner-output representation

The desired final parent graph is:

```text
START -> subject_planner_node -> route_after_subject_planner
```

The router then returns create and update `Send(...)` branches directly.

## Step 4: Migrate Existing-Subject Fanout And Update Input

Goal:

- make the full update path consume existing-classified `SubjectBucket`s

Refactor `fan_out_updates(...)`:

- stop reading `state.plan.relevant_for_update_links`
- select existing-classified buckets from `state.subjects`
- create one `Send("update_subagent", ...)` per existing bucket
- use `candidate_existing_id` to include exactly one existing profile
- include only messages listed by that bucket's `message_ids`
- do not send `state.plan`

Refactor `run_update_subgagent(...)`:

- accept the dictionary payload produced by `fan_out_updates(...)`
- pass the selected existing profile and supporting messages into
  `update_subgraph`
- stop reading `state.plan`
- stop passing `reasoning_summary_for_update`

Temporarily adapt `route_after_planner(...)`:

- decide update routing from existing-classified `state.subjects`
- call the migrated `fan_out_updates(...)` whenever existing buckets exist
- continue deciding create routing from the old `state.plan` until Step 5

This temporary hybrid router keeps both paths reachable while they migrate at
different times.

Remove the summary dependency from:

- `UpdateAgentState`
- `update_patches(...)`
- `patch(...)`

Use instead:

- the selected existing profile
- its supporting messages
- for repair, the failed candidate and validation errors

Keep stable:

- `apply_patch(...)`
- `validate(...)`
- `route_patches(...)`
- `human_repair(...)`
- `commit(...)`
- the one-existing-profile update-subgraph contract

Do after coding:

- review the implementation
- before writing tests, ask whether Step 4 and Step 5 should share one test pass

## Step 5: Create New-Subject Fanout And Adapt Create Input

Goal:

- make the full create path consume new-classified `SubjectBucket`s

Create `fan_out_creates(...)`:

- select new-classified buckets from `state.subjects`
- create one `Send("extract_subagent", ...)` per new bucket
- include exactly one subject bucket per branch
- include only messages listed by that bucket's `message_ids`
- never create one branch per supporting message

Refactor `run_extract_subgagent(...)`:

- accept the dictionary payload produced by `fan_out_creates(...)`
- pass one subject bucket and its supporting messages into `extract_subgraph`
- stop reading or constructing `state.plan`
- stop passing `reasoning_summary_for_create`

Refactor `ExtractAgentState`:

- stop inheriting the complete parent `MainState`
- carry only:
  - one subject bucket
  - supporting messages
  - an `existing` output dictionary containing the newly created profile so
    the parent `merge_profiles(...)` reducer can consume the wrapper result
  - mismatch, retry, or interrupt state still required
- do not carry the parent's complete `existing`, `subjects`, or obsolete
  `plan` into each create branch

Refactor `extract_node(...)` and `human(...)`:

- extract exactly one `UserProfile` for one subject branch
- use the subject label and supporting messages as context
- remove `new_person_count` and planner-summary dependencies
- replace old batch-count mismatch logic with the one-subject expectation
- preserve a human repair path for invalid or missing extraction results
- return the created profile under a new generated ID through the branch's
  `existing` output dictionary

Complete the temporary `route_after_planner(...)` migration:

- replace its old normal-node create destination with the `Send(...)` objects
  returned by `fan_out_creates(...)`
- decide both create and update routing from `state.subjects`
- leave `planner_node(...)` temporarily connected but no longer use
  `state.plan` for routing

This prevents the migrated create wrapper from being called with the old full
parent-state input while waiting for Step 6 and Step 7 cleanup.

Do after coding:

- review the implementation
- before writing tests, ask whether Steps 4 and 5 should share one test pass

## Step 6: Route Directly From Subject Buckets

Goal:

- finalize and rename the parent router after Step 5 has made
  `state.subjects` its only routing input

Refactor and rename `route_after_planner(...)` to
`route_after_subject_planner(...)`:

- preserve the subject-based behavior completed in Steps 4 and 5
- return one create `Send(...)` per new bucket through `fan_out_creates(...)`
- return one update `Send(...)` per existing bucket through
  `fan_out_updates(...)`
- support create-only, update-only, and mixed batches
- return `END` when no subjects exist
- allow the same supporting message to appear in several subject branches

Do after coding:

- verify both wrappers already accept the router's new payloads
- review the router before changing parent graph wiring

## Step 7: Replace The Old Planner In The Parent Graph

Goal:

- make the subject planner the only parent planning node

Change:

- rename `upstream_subject_node(...)` to `subject_planner_node(...)`
- remove `planner_node(...)` from `parent_builder`
- wire:

```text
START -> subject_planner_node -> route_after_subject_planner
```

- preserve the existing create and update result merge into parent `existing`

Do after coding:

- verify the graph compiles
- verify there is no parent route that still depends on `state.plan`

## Step 8: Remove Obsolete Planner State And Schemas

Goal:

- remove the old architecture only after all consumers have migrated

Remove:

- `CreateLink`
- `UpdateLink`
- `MessageSelectionOutput`
- `MainState.plan`
- `reasoning_summary_for_create`
- `reasoning_summary_for_update`
- obsolete imports, comments, and docstrings

Search the repository for every remaining dependency on:

- `state.plan`
- `new_person_count`
- retired planner schemas
- retired reasoning summaries

Update or retire tests and active documentation that describe the old
architecture.

Do after coding:

- review the cleanup
- confirm no working feature was removed with the obsolete structures

## Step 9: Build Focused Fanout And Wrapper Coverage

Goal:

- prove each migrated branch contract independently

Before writing tests:

- ask for approval
- decide whether update and create fanout tests should be grouped

Required update-path cases:

- one existing subject with one message
- one existing subject with several messages
- several existing subjects
- existing subject mentioned with no actionable update

Required create-path cases:

- one named new subject
- one unnamed new subject
- one new subject supported by several messages
- several new subjects

Required fanout assertions:

- one bucket produces one branch
- each branch receives only its supporting messages
- update branches receive exactly one existing profile
- shared messages may appear in multiple subject branches

## Step 10: Rebuild Parent Integration Coverage

Goal:

- prove the original mixed create+update limitation is fixed

Before writing tests:

- ask for approval
- consider combining related scenarios efficiently

Required scenarios:

- no detected subjects
- create-only batch
- update-only batch
- mixed create+update batch
- one shared message mentioning new and existing subjects
- repeated new subject across several messages
- later message updating a profile created during an earlier graph turn
- accumulated second-turn history using the intended checkpointed runner

The tests must prove:

- repeated mentions remain one branch per subject
- create and update fanout coexist in one parent run
- update no-op behavior remains valid
- committed create and update results merge into parent `existing`
- the old planner architecture is no longer required

## Execution Order

Continue from the completed Step 3 in this order:

1. migrate `fan_out_updates(...)` and the update wrapper/input
2. create `fan_out_creates(...)` and migrate the create wrapper/input
3. route directly from subject buckets
4. replace the old planner in the parent graph
5. remove obsolete planner state and schemas
6. build focused fanout and wrapper coverage
7. rebuild parent integration coverage

Do not remove old schemas before their consumers have migrated.

## Definition Of Success

Part 3 is complete when:

- `SubjectBucketList` is the only parent planning representation
- one subject always produces one create or update branch
- `fan_out_updates(...)` consumes existing subject buckets
- `fan_out_creates(...)` consumes new subject buckets
- the parent graph no longer calls `planner_node(...)`
- old planner schemas and reasoning summaries are removed
- create-only, update-only, mixed, and checkpointed multi-turn behavior work
- the project is ready for later identity-resolution and ambiguity handling
