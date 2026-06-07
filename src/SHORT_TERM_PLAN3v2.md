# SHORT_TERM_PLAN3v2

This file is the next short-term architectural plan after `SHORT_TERM_PLAN2.md`.

`SHORT_TERM_PLAN2.md` was mainly about building the current planner -> create/update subgraph architecture and getting it working end to end.

This new plan is about fixing a real limitation that appeared once the current architecture started passing stronger integration tests.

It is also a stepping stone toward the larger north-star architecture described in `memory_agent.drawio.xml`.

For the fuller architectural reasoning behind this refactor wave, see [ARCHITECTURAL_NOTE.md](/Users/mariofishman/projects/chatbot3/ARCHITECTURAL_NOTE.md).

This means:

- this file should contain real refactor steps for the codebase as it exists now
- but it should not try to implement the full `memory_agent.drawio.xml` architecture at once

## Short-Term Objective

The short-term objective of this plan is:

- preserve batch processing
- preserve the create/update split
- add a batch-level subject identity layer before create/update planning
- make repeated mentions of the same new person across a batch work correctly
- prepare the create path for a later per-person fanout architecture

This refactor is intentionally not a reset.

It should preserve the parts of the current architecture that are already working well:

- the update subgraph
- the update-side fanout pattern
- `route_after_planner(...)` as the current parent-side split point
- the parent `existing` merge contract
- the deterministic patch-validation-repair-commit loop

In other words:

- this plan should fix the current mixed create+update limitation
- while moving the code one layer closer to the north-star pipeline of:
  - subject detection
  - candidate retrieval
  - a simplified binary existing/new decision

## The Problem We Found

The current create-side planning contract is too weak for mixed batches where:

- one message introduces one or more new people
- later messages add more information about one of those same new people
- the same batch may also update already existing people

Right now, create planning is based on `CreateLink(message_id, new_person_count)`.

That lets the planner say:

- this message is relevant for creation
- this message mentions `N` new people

But it does not let the planner say:

- these two messages refer to the same new person
- these three messages together form the evidence bundle for one new person

So the architectural issue is upstream from `extract_node`.

The problem is not only extraction quality.
The problem is that the system does not yet have a batch-level identity layer for newly discovered people before they receive final `user_id`s.

## The Chosen Direction

The current preferred sequence is:

1. Add an upstream subject-identification and candidate-retrieval stage, then redesign create planning so its basic unit is one identified new person plus the list of supporting messages for that person.
2. After that person-centric create unit is stable, refactor create execution so each identified new person is processed independently in its own create run and then merged back into parent state.

Example:

- message 1 says: "I met Lucia Romero from Lima and Diego Salazar from Bogota. Philip de Haas is now based in Zurich."
- message 2 says: "Lucia Romero is a startup lawyer."
- message 3 says: "Diego Salazar is interested in fintech."

The upstream stage should first recognize that:

- Lucia in messages 1 and 2 is the same new person
- Diego in messages 1 and 3 is the same new person
- Philip is an already existing person

Then create planning should produce one unit for Lucia and one unit for Diego, instead of treating each message as if it introduced a separate new person.

Only after those per-person create units exist should the create path be refactored so Lucia and Diego can each be processed in separate create runs.

That means:

- first add a pre-planner-style subject-identification and candidate-retrieval stage
- then make create planning operate on explicit per-person units
- only after that, refactor create execution into a fanout architecture similar to the update path

## Why This Direction Was Chosen

### Why Not Message-At-A-Time Execution

One simple fix would be to run the whole parent flow one message at a time.

That would solve the identity problem with relatively little code change, because later messages could see earlier committed profiles from the same run.

But this likely makes:

- token usage worse
- latency worse
- batching weaker

So it is not the preferred direction.

### Why Subject Identification And Candidate Retrieval

This stage adds a pre-planner node that identifies the people mentioned in the batch and begins classifying them as:

- already existing people
- newly discovered people

This is valuable because it introduces the missing architectural layer:

- subject identification before downstream create/update planning

This is also a good foundation for future disambiguation work, even though Part 3 itself keeps only a binary existing/new decision.

### Why Person-Centric Create Planning

This change makes the create planning unit move from:

- message-centric

to:

- person-centric

Instead of `CreateLink(message_id, new_person_count)`, the planner should return something closer to:

- one identified new person
- a list of supporting `message_id`s for that person

This is stronger than just letting a create link point to multiple messages without naming the person.

It makes the person, not the message, the explicit planning unit.

### Why Create-Side Fanout Comes Afterward

Once create planning becomes person-centric, the create path can be refactored to mirror the update path more closely.

That means:

- one create unit per identified new person
- create-side fanout
- one extraction run per new person

This is attractive because the create path would then become structurally closer to the update path:

- identify target
- fan out
- process one target at a time
- merge back into parent state

But this should come after the identity/grouping fix, not before it.

## Refactor Goal

The main goal of this plan is:

- preserve batch processing
- preserve the create/update split
- but add enough batch-level subject identity so repeated mentions of the same new person can be grouped correctly before extraction

## Proposed Refactor Stages

These are intended as actual implementation stages, not only conceptual notes.

Each stage should:

- have one very short-term goal
- leave the codebase runnable
- prepare the next stage instead of trying to solve everything at once

### Stage 1: Add Batch-Level Subject Identification

Short-term goal:

- introduce one upstream place where the batch is analyzed in subject terms rather than only in message terms

Add a node before the main planner that looks at the batch of human messages and identifies subject mentions across the batch.

Its job is not yet to create final `UserProfile`s.

Its job is to produce subject-level buckets such as:

- existing subject bucket
- new subject bucket

Each bucket should collect:

- a subject label or provisional identity
- the supporting `message_id`s
- enough evidence to retrieve possible existing-profile matches and support downstream planning

For Part 3, the bucket should represent exactly one detected person.

The intended shape is:

- `subject_label: str`
- `message_ids: list[str]`
- `candidate_existing_id: str | None`
- `classification: Literal["existing", "new"]`

Meaning:

- `subject_label`
  - the detected person name or best available label from the batch
- `message_ids`
  - all message ids in the batch that refer to that same person
- `candidate_existing_id`
  - one chosen existing profile id when the subject is classified as existing
  - otherwise `None`
- `classification`
  - a binary Part 3 decision:
    - `existing`
    - `new`

Important Part 3 constraint:

- one `SubjectBucket` represents one person only
- no ambiguity state is included yet
- no clarification state is included yet
- if `classification == "existing"`, then `candidate_existing_id` should be set
- if `classification == "new"`, then `candidate_existing_id` should be `None`

At this stage, the bucket identity is temporary and batch-local.

It is not the final `user_id`.

Concrete code effect:

- add new state structures for batch-local subject units
- add a new upstream subject-bucket schema, likely in `state.py`
- extend `MainState` so the parent graph can carry those subject buckets
- keep `existing` as the same canonical committed store
- do not change final committed `existing` semantics yet
- do not change the update subgraph contract yet

Why this comes first:

- later stages need a stable upstream representation of subjects before create planning can become person-centric

Functions and classes affected first:

- `state.py`
  - `MainState`
  - new `SubjectBucket`-style schema
- parent graph in `graphv3.py`
  - a new upstream node before `planner_node(...)`

### Stage 2: Redefine The Create Planning Schema Around New-Person Units

Short-term goal:

- replace message-count-based create planning with person-based create planning

Replace the old message-centric create planning contract with a person-centric one.

The planner should no longer decide creation only as:

- this message creates `N` people

Instead, it should decide creation as:

- this identified new person should be created
- these message ids are the supporting evidence for that person

This is the explicit person-centric create-planning part of the plan.

Concrete code effect:

- replace or redesign `CreateLink`
- likely redesign `MessageSelectionOutput` so create-side planning is no longer based on `message_id + new_person_count`
- keep `UpdateLink` and the update-side part of `MessageSelectionOutput` as stable as possible
- stop relying on `new_person_count` as the main create-side grouping mechanism
- make the create plan point to one new identified subject plus supporting messages
- keep `UpdateLink` stable unless a later stage proves a change is truly needed

Why this comes second:

- the planner cannot emit person-centric create units until Stage 1 gives it subject-level input

Functions and classes affected here:

- `state.py`
  - `CreateLink`
  - `MessageSelectionOutput`
- `graphv3.py`
  - `planner_node(...)`

### Stage 3: Keep Update Planning Compatible With Existing IDs

Short-term goal:

- protect the working update path while the create side changes upstream

The update side already has stable `user_id`s and already supports multiple messages per target user through fanout.

So the update side should remain closer to the current design.

But it should be able to consume the upstream subject-identification layer when useful, while Part 3 still keeps the upstream decision binary rather than fully ambiguous-aware.

Concrete code effect:

- keep `UpdateLink` and update fanout behavior as stable as possible
- adapt the parent orchestration so update planning can coexist with the new create-side subject units
- preserve `run_update_subgagent(...)`, `update_subgraph`, and `merge_profiles(...)` contracts unless a concrete incompatibility appears
- preserve `fan_out_updates(...)` logic unless the new upstream subject layer forces a clearly better parent input shape

Why this comes here:

- once create planning changes, parent orchestration becomes mixed again
- this stage makes sure the refactor extends the current architecture instead of breaking the already working update half

Functions and classes that should remain mostly stable here:

- `UpdateLink`
- `fan_out_updates(...)`
- `run_update_subgagent(...)`
- update-side `UpdateAgentState`
- update subgraph nodes

### Stage 4: Refactor The Create Wrapper To Consume Person Buckets

Short-term goal:

- make the create wrapper accept the new person-centric planning unit without yet introducing full create fanout

After the planning schema changes, the create wrapper should stop thinking only in terms of flat create-relevant messages.

Instead, it should consume one create unit per identified new person.

At first, this can still feed the current create subgraph in a simpler grouped form.

That keeps the architecture moving forward without requiring immediate full fanout.

Concrete code effect:

- `run_extract_subgagent(...)` will likely need a new input contract
- `route_after_planner(...)` will need to route person-centric create units instead of only flat message-count-centric create links
- `planner_node(...)` output will now be consumed by `route_after_planner(...)` in a new way on the create side
- create-side filtering will happen by subject bucket rather than only by flat message ids
- the extract path may temporarily keep one batched run even after the planner schema changes
- the current extract subgraph can remain in place during this stage, but its input should become person-aware instead of only message-count-aware
- `extract_node(...)` should stop assuming create evidence is grouped only by `new_person_count` per message
- the create-side mismatch logic should be re-evaluated because count mismatch may no longer be the only or main create-side validation check
- `ExtractAgentState` may need small changes if the create-side plan or human clarification payload depends on the new person-centric create units

Why this comes fourth:

- Stage 2 changes what create planning outputs
- this stage is the smallest adapter that lets the current extract path consume that better output

Functions and classes explicitly affected here:

- `route_after_planner(...)`
- `run_extract_subgagent(...)`
- `extract_node(...)`
- possibly `ExtractAgentState`

### Stage 5: Add Create-Side Fanout

Short-term goal:

- make create execution symmetrical with update execution, one identified new person at a time

Once the per-person create unit is stable, refactor the create side into a fanout architecture similar to the update side.

That means:

- one create subgraph run per new identified person
- parallel or independently addressable create work
- deterministic merge of committed new profiles back into parent `existing`

This would make create and update more symmetrical.

Concrete code effect:

- introduce create-side `Send(...)` fanout or an equivalent worker-style split
- process one new identified subject per create run
- merge committed newly created profiles back into parent state safely
- redesign the create wrapper around one-person-per-run execution
- likely redesign the current batched assumptions inside `extract_subgraph`

Why this comes last:

- fanout is easier only after the create unit itself is stable
- otherwise the refactor would be changing identity, planning, and execution shape all at once

Functions and classes explicitly affected here:

- `run_extract_subgagent(...)` or its replacement
- create-side graph wiring in `graphv3.py`
- `route_after_planner(...)` create branch routing
- possibly `ExtractAgentState` if one-create-run-per-person needs a narrower state contract

## Suggested Implementation Order

1. Add the new batch-local subject structures in state.
2. Add the pre-planner / subject-identification node.
3. Redesign the create-side planner output around per-person create units.
4. Adapt the parent routing logic to consume the new create units.
5. Adapt the create wrapper to use subject buckets.
6. Re-run and update the mixed create+update integration test.
7. Only after that, refactor create execution toward fanout.

This order matters.

The mixed create+update limitation should be solved before the create path is made more parallel.

Practical reading of the order:

- Stages 1 and 2 fix the representation problem
- Stages 3 and 4 adapt the current graph to that better representation
- Stage 5 improves execution shape after the representation is already correct

Concrete reading of what should and should not be left unchanged:

- `CreateLink` cannot stay as it is
- the create-side part of `MessageSelectionOutput` cannot stay as it is
- `planner_node(...)` cannot stay as it is on the create side
- `route_after_planner(...)` cannot stay as it is on the create side
- `run_extract_subgagent(...)` cannot stay as it is
- `extract_node(...)` cannot keep relying only on `new_person_count`-style create grouping

At the same time:

- `UpdateLink` should stay close to its current form
- `fan_out_updates(...)` should stay close to its current form
- `run_update_subgagent(...)` should stay close to its current form
- the update subgraph should stay close to its current form
- `merge_profiles(...)` should stay close to its current form

## Do Not Break

The following currently working features should be protected during this refactor:

- create-only routing should still work
- update-only routing should still work
- mixed parent routing should still work
- the update subgraph should still work as it works now
- update-side fanout should still work as it works now
- reducer-based merging into parent `existing` should still work as it works now
- create-side mismatch and human fallback should not disappear silently during the create refactor

The highest-risk break points are:

- `MessageSelectionOutput`
- `planner_node(...)`
- `route_after_planner(...)`
- `run_extract_subgagent(...)`
- `extract_node(...)`

Safe refactor order:

1. change upstream create-side structures first
2. adapt parent routing second
3. adapt the create wrapper and extract path third
4. keep update internals unchanged unless a concrete incompatibility appears

## How The Older Ideas Fit Into This Plan

The older ideas from `SHORT_TERM_PLAN3.md` are still useful, but they belong after or alongside this refactor in the right order.

### Stronger Create Validation

This is still needed.

But it is downstream work.

Before stronger validation can matter, the system first has to group the right messages into the right person buckets.

So stronger create validation should happen after the identity/grouping fix starts working.

In other words:

- do not rewrite `extract_node(...)` first
- first fix what evidence bundle reaches `extract_node(...)`

### Smarter Create Repair

This is also still needed.

Once create extraction is person-centric, repair can also become more person-centric:

- missing person
- extra person
- merged people
- wrongly split people

That repair work becomes easier to reason about once the input units are per-person instead of per-message counts.

### Narrower Planner Context

This old idea is even more relevant now.

The pre-planner identity stage can help narrow planner context by turning a flat message batch into cleaner subject-level buckets.

So this old idea is not separate from the new refactor.

It is partly enabled by it.

### Better Human Clarification UX

This remains useful but secondary.

It should come after the architecture can correctly represent repeated new-person mentions in the first place.

Once the person-bucket structure exists, human clarification can also become more targeted:

- clarify this one bucket
- clarify whether these two mentions are the same person
- clarify whether this subject is new or existing

## Concrete Next Architectural Question

The next important design question is:

- what exact schema should the pre-planner output return?

That schema needs to be good enough to support:

- batch-level subject identity
- create/update separation
- future create fanout

without overcomplicating the current code more than necessary.

This is the first real design step of this plan.

It is more important than prematurely rewriting the create subgraph itself.

It should also be designed so it fits the current codebase rather than fighting it.

More specifically, the new upstream schema should be introduced in a way that still feels continuous with:

- `MainState`
- `MessageSelectionOutput`
- parent routing in `graphv3.py`
- reducer-based merging into `state.existing`

## Relationship To `memory_agent.drawio.xml`

This plan is not the full implementation of `memory_agent.drawio.xml`.

It is a narrower stepping stone toward it.

More specifically, this plan is intended to move the current code closer to these north-star nodes:

- subject and fact detection
- candidate retrieval / filtering
- identity resolution
- action proposal

But this plan does not yet try to fully implement:

- the entire non-simple-fact scope classification branch
- linked-entity workflows
- full worker/task-queue decomposition
- the complete relational-memory direction

That larger work should remain outside the scope of this short-term plan.

## Practical Scope Of This Plan

This file is the explicit short-term refactor direction for the next wave of work.

It is not yet the final line-by-line implementation checklist, but it is intended to be concrete enough to drive implementation order.

In short:

- first fix batch-level identity for newly discovered people using subject identification plus person-centric create planning
- then refactor create execution toward create-side fanout
- then improve validation, repair, and human clarification on top of that stronger structure
