# SHORT_TERM_PLAN3v3

This file is the executable roadmap for Part 3 of the project.

Its purpose is not to preserve architectural reasoning.

Its purpose is to define the refactor in a precise order that can be followed step by step without losing track of:

- what to change
- what to leave stable
- what to test after each change

For the full architectural reasoning, see:

- [ARCHITECTURAL_NOTE.md](/Users/mariofishman/projects/chatbot3/ARCHITECTURAL_NOTE.md)

## Part 3 Goal

Fix the mixed create+update limitation by changing the create side from a message-count-based design to a person-centric design, while keeping the current update path working.

## Scope Boundary

Part 3 includes:

- subject detection across the batch
- candidate retrieval from `state.existing`
- binary classification only:
  - `existing`
  - `new`
- person-centric create planning
- adaptation of the current create wrapper and extract path
- later, create-side fanout

Part 3 does not include:

- ambiguity handling
- clarification flow for subject identity
- non-simple fact taxonomy
- linked-entity workflows
- relational memory expansion

## Stable Parts

These should remain stable unless a concrete incompatibility appears:

- `UpdateLink`
- `fan_out_updates(...)`
- `run_update_subgagent(...)`
- `planner_node(...)` update-side reasoning and `reasoning_summary_for_update`
- `update_subgraph`
- `merge_profiles(...)`
- update-side validation / patch / repair / commit flow
- current update-side tests and update-side integration behavior

## Main Break Risks

The highest-risk create-side break points are:

- `MainState`
- `CreateLink`
- `MessageSelectionOutput`
- `planner_node(...)`
- `route_after_planner(...)`
- `run_extract_subgagent(...)`
- `extract_node(...)`
- `human(...)`
- `ExtractAgentState`
- parent graph wiring in `parent_builder`

## Do Not Break

While refactoring the create side, preserve these currently working features:

- update-only parent routing still produces only update `Send(...)` branches
- create-only parent routing still reaches the create path cleanly
- mixed parent routing still supports one create path plus one or more update branches
- `fan_out_updates(...)` still groups update messages by existing `user_id`
- `run_update_subgagent(...)` still passes one-user slices into `update_subgraph`
- `merge_profiles(...)` still merges returned one-user committed slices correctly
- create mismatch and human fallback still exist unless deliberately replaced

Safe execution order:

1. change create-side data structures first
2. add the new upstream node and parent state field
3. adapt planner output and parent routing
4. adapt the create wrapper and extract-side mismatch logic
5. add create-side fanout only after the person-centric create path is green

## Step 1: Define The New Upstream Schema

Goal:

- define the exact schema for one detected person in the batch

Output of this step:

- a concrete `SubjectBucket` model in `state.py`

Required shape:

- `subject_label: str`
- `message_ids: list[str]`
- `candidate_existing_id: str | None`
- `classification: Literal["existing", "new"]`

Rules:

- one `SubjectBucket` = one person
- `classification == "existing"` -> `candidate_existing_id` must be set
- `classification == "new"` -> `candidate_existing_id` must be `None`

Do after coding:

- review `state.py` for consistency
- add or update tests for the new schema if needed
- verify `MainState` and `ExtractAgentState` can carry this schema cleanly

## Step 2: Extend Parent State

Goal:

- let the parent graph carry subject buckets before planning

Change:

- extend `MainState` with a field for the upstream subject buckets

Do not change yet:

- `existing`
- update-side state models
- update-side reducer behavior

Do after coding:

- verify the graph still compiles
- verify existing planner tests still fail only for the expected create-side reasons

## Step 3: Add The Upstream Subject Node

Goal:

- add a new node before `planner_node(...)`

Its job:

- analyze the batch of human messages
- group repeated mentions of the same person
- retrieve and filter existing-profile candidates from `state.existing`
- choose one existing candidate id when applicable
- return binary `existing/new` classification only

Graph change in this step:

- add the new upstream node to `parent_builder`
- wire `START -> upstream_subject_node -> planner`
- keep the rest of the parent graph unchanged for now

Do not do yet:

- ambiguity handling
- human clarification
- full fact taxonomy

Do after coding:

- test one repeated-new-person case
- test one clearly-existing-person case
- verify `planner_node(...)` can still run unchanged when fed the new state field

## Step 4: Redesign The Create-Side Planner Output

Goal:

- stop representing create work as `message_id + new_person_count`

Change:

- redesign `CreateLink`
- redesign the create-side part of `MessageSelectionOutput`

New create-side unit:

- one identified new person
- supporting message ids for that person

Keep stable:

- `UpdateLink`
- update-side part of `MessageSelectionOutput` as much as possible

Do after coding:

- review `planner_node(...)` prompt and output shape
- update planner tests
- update state-model tests if the create-side planner schema changed there

## Step 5: Rewrite `planner_node(...)` For The New Split

Goal:

- make `planner_node(...)` consume upstream subject buckets instead of doing all create reasoning directly from raw messages

Planner responsibility after this step:

- use subject buckets
- decide create/update outputs in the new schema
- keep summaries short and factual
- keep update-side planning compatible with stable existing `user_id`s

Do not let planner do:

- extraction
- patching
- message rewriting

Do after coding:

- test create-only
- test update-only
- test planner output for repeated new person across several messages

## Step 6: Adapt `route_after_planner(...)`

Goal:

- make parent routing consume the new create-side planning unit

Change:

- keep update routing behavior close to current behavior
- change create routing so it works from person-centric create units
- make sure update planning and create planning can coexist in the same parent run

Keep stable:

- update-side `Send(...)` behavior
- `fan_out_updates(...)` implementation

Do after coding:

- verify:
  - create-only routing
  - update-only routing
  - mixed routing
- verify no regression in current update-path integration coverage

## Step 7: Adapt `run_extract_subgagent(...)`

Goal:

- make the create wrapper consume person-centric create units

Change:

- stop filtering only by flat create-relevant message ids
- build create-side input from one identified person plus that person’s supporting messages

This step is the adapter between:

- new parent planning output
- current create subgraph

Refactor targets in this step:

- `run_extract_subgagent(...)`
- any create-side state preparation passed into `extract_subgraph`
- possibly `ExtractAgentState` if grouped person context needs a dedicated field

Do after coding:

- inspect the sub-state shape carefully
- verify no update-side fields are broken
- verify create-only integration still passes after the adapter change

## Step 8: Adapt `extract_node(...)`

Goal:

- make the current create subgraph accept grouped evidence per person

Change:

- stop relying only on `new_person_count` per message
- consume grouped evidence for one or more identified new people

Re-evaluate:

- current count-based mismatch logic
- whether it still works unchanged
- whether it needs to become person-count-based instead of message-count-based

Refactor targets in this step:

- `extract_node(...)`
- `human(...)` if the mismatch prompt must reflect grouped person evidence
- any create-side retry assumptions that still depend on per-message counts

Do after coding:

- run create-only integration test
- run mixed create+update integration test
- verify human fallback still has enough context to repair create mismatches

## Step 9: Rebuild The Mixed Create+Update Test

Goal:

- prove the original architectural limitation is fixed

Required test case:

- one shared message mentions:
  - one or more new people
  - one existing person
- later messages add more facts about those same new people
- another message updates the existing person

The test should prove:

- repeated new-person mentions are grouped correctly
- existing-person updates still route correctly
- create and update accumulation can coexist in one batch
- no currently working update-only behavior regressed while enabling the mixed case

## Step 10: Add Create-Side Fanout

Goal:

- process one identified new person per create run

Change:

- introduce create-side `Send(...)` fanout or equivalent split
- one create run per new person
- merge committed new profiles back into parent `existing`

Refactor targets in this step:

- create-side routing in `route_after_planner(...)`
- the create wrapper so one branch handles one person
- create-side graph/result accumulation back into parent state

Do this only after:

- Steps 1 through 9 are green

Do after coding:

- integration test with more than one new person
- verify reducer merge behavior still works
- verify mixed create+update still works after create fanout is introduced

## Execution Rule

Do not skip ahead.

Use this order:

1. schema
2. parent state
3. upstream subject node
4. create-side planner schema
5. planner node
6. router
7. create wrapper
8. extract node
9. mixed integration test
10. create fanout

## Definition Of Success

Part 3 is successful when:

- repeated mentions of the same new person across a batch no longer break create behavior
- update-side behavior still works
- mixed create+update routing still works
- the codebase is ready for a later Part 4 that adds ambiguity handling and clarification
