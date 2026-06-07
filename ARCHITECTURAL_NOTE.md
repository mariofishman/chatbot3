# Architectural Note

This note records the architectural issue discovered after the current `graphv3.py` planner/create/update architecture started passing stronger integration tests.

It should be read together with:

- [SHORT_TERM_PLAN3v2](src/SHORT_TERM_PLAN3v2.md)
- [memory_agent.drawio.xml](memory_agent.drawio.xml)
- [LOGBOOK.md](LOGBOOK.md) Entry of June 7th.

This note is intentionally more explanatory than the short-term plan.

Its purpose is to preserve the full reasoning behind the next refactor wave, so the project can recover the architectural context later without depending on memory of the original discussion.

## What This Note Is About

The current codebase already has several parts that work well:

- the update subgraph
- the update-side fanout pattern
- `route_after_planner(...)` as the current parent-side create/update split point
- the parent `existing` merge contract
- the deterministic patch-validation-repair-commit loop

So this note is not about throwing away the architecture and starting over.

It is about identifying the specific upstream limitation that is now blocking stronger mixed create+update behavior.

## The Specific Problem

The current mixed create+update limitation appears when:

- one batch contains repeated mentions of the same new person
- one or more messages also update already existing people

Example:

- `hm_001`: "I met Lucia Romero from Lima and Diego Salazar from Bogota. Philip de Haas is now based in Zurich."
- `hm_002`: "Lucia Romero is a startup lawyer."
- `hm_003`: "Diego Salazar is interested in fintech."

The current planner can express create-side work only as:

- one `message_id`
- one `new_person_count`

That is not enough to express:

- Lucia in `hm_001` and Lucia in `hm_002` are the same new person
- Diego in `hm_001` and Diego in `hm_003` are the same new person

So the create-side representation is too message-centric.

The problem is upstream from `extract_node(...)`.

The problem is not only extraction quality.

The problem is that the system does not yet have a batch-level identity layer for newly discovered people before they receive final `user_id`s.

Right now, that limitation flows through the current parent orchestration:

- `planner_node(...)` still reasons mostly in message-centric terms for create
- `route_after_planner(...)` then routes create and update work using that planner output

So the refactor is not only about planner prompts.
It also affects the shape of what `route_after_planner(...)` needs to route.

## Why This Matters

This limitation is not just a small create-path bug.

It means the current architecture is still good enough for:

- create-only messages
- update-only messages
- batch updates for already known users

But it is not yet rich enough for:

- mixed create+update batches where new people are mentioned repeatedly across messages before they have final ids

So the next architectural work is not only "finish one more integration test."

The next architectural work is to decide how new-person identity should be represented across a batch before those people become committed profiles.

## Architectural Conclusion

The next refactor should not start by making `extract_node(...)` smarter.

It should start by splitting the current top-level planner responsibilities into more explicit upstream stages:

1. subject detection
2. candidate retrieval / filtering
3. binary existing-vs-new classification

This is consistent with the north-star architecture in `memory_agent.drawio.xml`.

More concretely:

- subject detection should identify people mentioned in the batch
- candidate retrieval should narrow relevant existing profiles for those subject mentions
- the upstream classification should decide only:
  - existing
  - new

For Part 3, that is enough.

Ambiguous cases and human clarification are intentionally deferred to a later phase.

So the real refactor is not simply “make the planner prompt smarter.”

The real refactor is to decompose the current planner into more explicit upstream stages.

That decomposition should still preserve the current architectural role of `route_after_planner(...)`, but it will likely change the kind of create-side unit that the router receives.

## The Chosen Direction

The current preferred sequence is:

1. add an upstream subject-identification and candidate-retrieval stage, then redesign create planning so its basic unit is one identified new person plus the list of supporting messages for that person
2. after that person-centric create unit is stable, refactor create execution so each identified new person is processed independently in its own create run and then merged back into parent state

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

As a consequence, `route_after_planner(...)` will eventually need to route:

- update-side work much as it already does now
- but create-side work using person-centric create units instead of only message-count-centric create links

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

This is also a good foundation for later disambiguation work, even though Part 3 itself keeps only a binary existing/new decision.

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

The main goal of this refactor direction is:

- preserve batch processing
- preserve the create/update split
- but add enough batch-level subject identity so repeated mentions of the same new person can be grouped correctly before extraction

This is intentionally not a reset.

The current direction should preserve the parts of the architecture that already work well:

- the update subgraph
- the update-side fanout pattern
- the parent `existing` merge contract
- the deterministic patch-validation-repair-commit loop

## Short-Term Direction

The short-term refactor should proceed in this order:

1. add batch-level subject identification and candidate retrieval
2. redesign create planning so the unit is one identified new person plus supporting messages
3. keep the current update path stable while the create path changes
4. adapt the create wrapper to consume person-centric create units
5. only then refactor create execution into one-create-unit-per-person fanout

This order matters.

The mixed create+update limitation should be solved before the create path is made more parallel.

## Staged Refactor Logic

These stages are not only conceptual notes.

They are meant to be actual implementation stages, each leaving the codebase runnable and each preparing the next stage instead of trying to solve everything at once.

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
- do not change final committed `existing` semantics yet
- do not change the update subgraph contract yet

Why this comes first:

- later stages need a stable upstream representation of subjects before create planning can become person-centric

### Stage 2: Redefine The Create Planning Schema Around New-Person Units

Short-term goal:

- replace message-count-based create planning with person-based create planning

Replace the old message-centric create planning contract with a person-centric one.

The planner should no longer decide creation only as:

- this message creates `N` people

Instead, it should decide creation as:

- this identified new person should be created
- these message ids are the supporting evidence for that person

Concrete code effect:

- replace or redesign `CreateLink`
- stop relying on `new_person_count` as the main create-side grouping mechanism
- make the create plan point to one new identified subject plus supporting messages
- keep `UpdateLink` stable unless a later stage proves a change is truly needed

Why this comes second:

- the planner cannot emit person-centric create units until Stage 1 gives it subject-level input

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

Why this comes here:

- once create planning changes, parent orchestration becomes mixed again
- this stage makes sure the refactor extends the current architecture instead of breaking the already working update half

### Stage 4: Refactor The Create Wrapper To Consume Person Buckets

Short-term goal:

- make the create wrapper and the current `extract_subgraph` accept the new person-centric planning unit without yet introducing full create fanout

After the planning schema changes, the create wrapper should stop thinking only in terms of flat create-relevant messages.

Instead, it should consume one create unit per identified new person.

At first, this can still feed the current create subgraph in a simpler grouped form.

That keeps the architecture moving forward without requiring immediate full fanout.

Concrete code effect:

- `run_extract_subgagent(...)` will likely need a new input contract
- `route_after_planner(...)` will need to route person-centric create units instead of only message-count-centric create links
- create-side filtering will happen by subject bucket rather than only by flat message ids
- the extract path may temporarily keep one batched run even after the planner schema changes
- the current `extract_subgraph` can remain in place during this stage, but its input contract should become person-aware instead of only message-count-aware
- `extract_node(...)` should stop assuming create evidence is grouped only by `new_person_count` per message and should start consuming grouped evidence per identified new person
- the create-side mismatch / repair logic should be updated only as needed so it still works with the new per-person grouped input

Why this comes fourth:

- Stage 2 changes what create planning outputs
- this stage is the smallest adapter that lets the current parent routing layer, create wrapper, and `extract_subgraph` consume that better output

### Stage 5: Add Create-Side Fanout

Short-term goal:

- make create execution symmetrical with update execution, one identified new person at a time

Once the per-person create unit is stable, refactor the create side into a fanout architecture similar to the update side.

That means:

- one create subgraph run per new identified person
- parallel or independently addressable create work
- deterministic merge of committed new profiles back into parent `existing`

Concrete code effect:

- introduce create-side `Send(...)` fanout or an equivalent worker-style split
- process one new identified subject per create run
- merge committed newly created profiles back into parent state safely

Why this comes last:

- fanout is easier only after the create unit itself is stable
- otherwise the refactor would be changing identity, planning, and execution shape all at once

## Suggested Implementation Order

1. Add the new batch-local subject structures in state.
2. Add the pre-planner / subject-identification node.
3. Redesign the create-side planner output around per-person create units.
4. Adapt the parent routing logic to consume the new create units.
5. Adapt the create wrapper to use subject buckets.
6. Re-run and update the mixed create+update integration test.
7. Only after that, refactor create execution toward fanout.

Practical reading of the order:

- Stages 1 and 2 fix the representation problem
- Stages 3 and 4 adapt the current graph to that better representation
- Stage 5 improves execution shape after the representation is already correct

## How The Older `SHORT_TERM_PLAN3.md` Ideas Fit Here

The older ideas are still useful, but they belong at the right level and in the right order.

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

It should come later, not in Part 3.

Part 3 is intentionally allowing a simpler and riskier binary choice:

- existing
- new

even when that may occasionally be wrong.

## Relationship To `memory_agent.drawio.xml`

This note does not mean the project should now implement the full north-star architecture all at once.

It means the next refactor wave should move the current implementation one layer closer to it, especially toward:

- subject and fact detection
- candidate retrieval / filtering
- the early part of identity handling, but only in a simplified binary form for now

But the current short-term plan does not yet try to fully implement:

- a full ambiguity / clarification workflow
- the entire non-simple-fact scope classification branch
- linked-entity workflows
- full worker/task-queue decomposition
- the complete relational-memory direction

The current direction remains incremental.

## Practical Scope

This note is the fuller architectural reasoning for the next wave of work.

It is not the final line-by-line implementation checklist, but it is intended to preserve the complete logic behind the refactor direction.

In short:

- first fix batch-level identity for newly discovered people using subject identification plus person-centric create planning
- then refactor create execution toward create-side fanout
- then improve validation, repair, and human clarification on top of that stronger structure
- leave ambiguity handling, clarification, and fuller identity-resolution logic to a later phase
