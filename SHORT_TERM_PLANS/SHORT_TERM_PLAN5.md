# Short-Term Plan 5: Controlled Graph Memory Persistence

## Purpose

Build the persistence layer that separates thread-scoped conversation state
from app-user-scoped graph memory.

This is the phase where `existing` user profiles stop being only local graph
state and become durable application data. Persisted memory is writable from
the point of view of one application user.

The chosen Stage 5 direction is:

```text
existing graphv3 create/update workflow
  -> app-user-scoped persistence boundary
  -> LlamaIndex graph/vector retrieval
  -> LLM persistence/update planning for graph memory
  -> custom validated graph writer
  -> Neo4j graph persistence
```

Required architecture reference:

```text
memory_agent.drawio.xml
```

Future readers should review that diagram before implementing Stage 5. It
contains the intended subject detection, candidate retrieval, duplicate
reduction, ambiguity reduction, and memory-routing logic that this plan should
build toward.

## Already Completed Foundations From Part 3

Do not rebuild the graph behavior completed in `SHORT_TERM_PLAN3v5.md`.

The current `graphv3.py` already has:

- subject detection into `SubjectBucketList`
- create/update routing by subject
- create fanout and update fanout
- one new subject per extraction branch
- one existing profile per update branch
- create-side candidate, retry, human repair, and commit boundaries
- update-side patch proposal, patch application, validation, retry, human
  repair, and commit boundaries
- no-op update behavior
- explicit submit/decline repair envelopes
- interrupt resume by ID
- parent reducer merge-back for committed profiles

Stage 5 should not replace those mechanics. It should add a persistence and
retrieval layer around them.

## Problem

Today, LangGraph checkpoint state gives each thread its own execution memory.
That is correct for `messages`, `subjects`, pending interrupts, and graph
resume state.

But user profiles should eventually behave like app-user-scoped application
data with an optional identity-linking layer:

- a profile created in one thread should be available in another thread for
  the same application user
- a profile created or updated from John's conversations should not overwrite
  Paul's profile data, even if both are talking about Peter
- several app-user-scoped profile records may later be linked as likely
  references to the same real-world person
- application users should only retrieve profile records connected to their own
  app-user scope
- messages from different threads should remain isolated
- duplicate profiles should be reduced
- ambiguous identity decisions should have richer context
- profile retrieval should help the subject planner decide whether someone is
  new or existing
- facts, entities, relationships, and properties should be stored through a
  controlled graph-memory write path rather than arbitrary database writes

## Scope

### Controlled Graph Memory Flow

Stage 5 should build the persistence workflow around the existing graph:

1. Receive the current app user identity from the Part 4 API boundary.
2. Retrieve candidate app-user-scoped memories before graph execution or before
   subject planning.
3. Provide retrieved candidates to the existing graph so it can classify
   subjects and reduce duplicates more intelligently.
4. Let the existing create/update subgraphs produce committed `UserProfile`
   results.
5. Translate committed profile changes into a structured graph-memory update
   plan.
6. Validate that update plan against graph primitives and the manual schema.
7. Convert approved graph primitives into Cypher.
8. Persist the result in Neo4j.
9. Retrieve persisted memory in later graph runs.

LangGraph should orchestrate this flow. It should not become the retrieval or
database layer itself.

If Stage 5 later adds entity/relationship extraction beyond the existing
`UserProfile` fields, that work should be scoped as graph-memory enrichment,
not as a replacement for the existing create/update subgraphs.

### Retrieval Before Write

Before creating or updating persisted memory, retrieve existing relevant memory
for the active `app_user_id`.

Use LlamaIndex for:

- graph retrieval
- vector retrieval
- hybrid retrieval
- graph traversal / GraphRAG context

The retrieved context should help the existing graph decide whether a subject
refers to an existing app-user-scoped memory, a new memory, or information that
should not produce a persistence write.

### Controlled Writer Layer

Do not let the LLM generate arbitrary Cypher.

After the existing graph produces committed profile changes, the persistence
planner may produce a structured graph update plan using a small set of
validated graph primitives, such as:

- `merge_node`
- `merge_edge`
- `update_property`
- `expire_fact`
- `create_fact`
- `no_op`

A custom writer layer should validate those primitives against the manually
defined schema and only then generate Cypher for Neo4j.

This writer layer is the safety boundary between model reasoning and database
mutation.

### App-User-Scoped UserProfile Persistence

Separate persistent profile memory from thread-scoped conversation state.

- `messages` remain thread-scoped
- `subjects` remain thread-scoped
- pending interrupts remain thread-scoped
- committed `existing` profiles move toward persisted profile records scoped to
  an application user
- one application user may have many persisted `UserProfile` records
- two application users may each have their own different `UserProfile` record
  for the same real-world person
- updates from one app user's conversations must not mutate another app user's
  profile record
- a later identity-linking layer may connect multiple app-user-scoped records
  that likely refer to the same real-world person

After implementing this separation, add integration tests proving that a
profile created in one thread is recognized and updated from another thread
for the same application user, without sharing either thread's message history.
Also add tests proving that a different app user with a different thread does
not see or update the first user's profile record.

Minimal schema direction:

```text
app_users
- app_user_id

user_profiles
- profile_id
- app_user_id
- UserProfile fields

identity_entities
- identity_entity_id
- optional canonical or dedup metadata

profile_identity_links
- profile_id
- identity_entity_id
- confidence / source / relationship
```

For now, `app_user_id` can be dev/manual and selected by the frontend or API.
`SHORT_TERM_PLAN4.md` should already provide this temporary identity source in
the request boundary. Later authentication should provide the real
`app_user_id` without requiring a database redesign.

Important: `identity_entities` and `profile_identity_links` are not the first
writable target. They are optional later layers for deduplication and ambiguity
reduction. The first persistence slice should write and update app-user-scoped
`UserProfile` records.

### Initial Manual Graph Schema

Stage 5 should start with a manually governed schema. The LLM can populate the
schema but must not freely change it.

Initial candidate nodes:

- `AppUser`
- `UserProfile`
- `Company`
- `Project`
- `Meeting`
- `Preference`

Initial candidate relationships:

- `HAS_PROFILE_RECORD`
- `WORKS_AT`
- `KNOWS`
- `INTRODUCED`
- `PREFERS`
- `ATTENDED`
- `MENTIONED_IN_THREAD`

This schema can evolve later, but Stage 5 should keep schema changes manual.

### Persistence During Parallel Human Repair

Parallel update branches may reach `human_repair` at different times. A
completed branch can become visible in `graph.get_state(config).values` even
while other branches in the same superstep remain interrupted.

Part 3 already solved the human repair, interrupt, resume, and merge-back
behavior. Stage 5 only decides how completed profile outputs are harvested and
upserted into app-user-scoped persistence.

The persistence layer should explicitly upsert each completed app-user-scoped
profile without waiting for every sibling interrupt to be resolved.

The frontend/FastAPI layer from Part 4 should already support resolving
interrupts one at a time by interrupt ID. This persistence layer must build on
that behavior by deciding when completed profiles are harvested and upserted
into app-user-scoped profile storage.

After each resumed invocation, the persistence layer should:

- use the invocation result's `__interrupt__` collection to identify only the
  branches that still require human input
- use `graph.get_state(config).values` to inspect the latest accumulated state
  and harvest app-user-scoped profiles completed by that response
- keep downstream graph execution blocked until every branch in the parallel
  superstep completes

The LangGraph checkpointer persists thread-scoped execution state and durable
task-level writes. It does not automatically write completed profiles to the
application profile database. Profile writes must therefore be explicit and
idempotent so retries or resumed nodes cannot create duplicates or corrupt
already-persisted profile records.

### Identity Retrieval And Ambiguity Reduction

Use the persistence layer to support the already-built subject planner with
better retrieval context, reduce duplicates, and handle ambiguous information
more deliberately.

This section should be implemented with `memory_agent.drawio.xml` open as a
reference. The XML diagram contains the more detailed logic for identifying
subjects, retrieving candidate memories, deciding whether a subject is new or
existing, and reducing ambiguity before writing to memory.

Stage 5 should include:

- retrieving candidate existing profiles before subject planning
- comparing new mentions against stored profiles
- reducing duplicate profiles within one app user's profile records
- reducing ambiguous new/existing classification
- detecting when new conversation data may refer to an existing app-user-scoped
  `UserProfile` instead of creating a duplicate
- routing uncertain data through a conservative persistence create/update/no-op
  decision instead of blindly writing it
- preserving ambiguous evidence in a controlled way when it cannot yet be
  safely merged into an existing profile record
- using graph relationships to distinguish similarly named people
- using LlamaIndex retrieval over Neo4j-backed graph memory

Later work may include:

- linking similar profile records across app users without merging their
  app-user-scoped facts
- richer entity resolution across users

Schema/ontology evolution proposals are not part of Stage 5. They belong to
`SHORT_TERM_PLAN6.md`.

This is where the identity and ambiguity-reduction ideas from
`memory_agent.drawio.xml` should become concrete.

## Likely Architecture Direction

Possible staged path:

1. Review the completed Part 3 contracts and define what persistence receives
   from committed create/update outputs.
2. Define the manual initial graph schema and graph primitives.
3. Define a repository/writer interface for app-user-scoped memory writes.
4. Reuse the dev/manual `app_user_id` boundary introduced in
   `SHORT_TERM_PLAN4.md`.
5. Set up Neo4j as the graph persistence backend.
6. Add LlamaIndex retrieval over the graph memory.
7. Add retrieval-before-write to the existing graph workflow.
8. Add duplicate/ambiguity reduction logic based on retrieved candidates.
9. Add LLM graph-memory update planning with structured primitives for
   persistence writes.
10. Add the custom writer layer that validates primitives before Cypher.
11. Save committed memory changes under the active app-user scope after graph
    execution or after each repaired branch completion.
12. Add tests for same-app-user cross-thread profile reuse.
13. Add tests proving another app user's profile record is not read or mutated.
14. Add tests for duplicate-risk and ambiguous-subject conversations described
    by `memory_agent.drawio.xml`.
15. Explicitly defer cross-user identity linking unless a minimal safe version
    is needed after app-user-scoped persistence works.

## Non-Goals

- Do not build unrelated frontend UI polish here. UI changes are allowed when
  needed to select, display, or debug the user/session/persistence boundary.
- Do not move thread-scoped messages into shared profile storage.
- Do not rebuild Part 3 create/update/retry/human-repair behavior.
- Do not allow arbitrary LLM-generated Cypher.
- Do not implement automatic ontology/schema evolution in Stage 5. It belongs to a later stage.
- Do not let the model freely create new node labels, relationship types, or
  property names outside the manually governed schema.
- Do not use persistence to hide graph bugs.

Graphiti/Zep may remain a useful external reference for how conversational
memory systems can work. Evaluate it and read it as referrence.

### Deferred Within Stage 5: Cross-User Identity Linking

Cross-user identity linking belongs to the Stage 5 memory/persistence domain,
but it does not need to be part of the first persistence slice.

The first writable target should remain app-user-scoped `UserProfile` records.
John's record for Peter and Paul's record for Peter should not overwrite each
other.

After app-user-scoped persistence works, a later identity layer may link
several users' profile records when they appear to describe the same real-world
person. That layer should preserve each app user's facts while adding a
separate identity relationship between records.

This is different from Stage 6 schema evolution. Identity linking connects
records that fit the existing memory schema; Stage 6 proposes changes to the
schema itself.

Controlled schema evolution belongs to Stage 6, after the basic graph memory
layer works reliably with a manually governed schema.

## Definition Of Done

This phase is done when:

- shared profile persistence is explicitly separated from thread checkpoints
- persisted `UserProfile` records are scoped to one app user as their first
  writable boundary
- Neo4j stores the initial graph memory schema
- LlamaIndex retrieves relevant graph/vector context before writes
- graph retrieval can provide candidates to graph execution
- duplicate-risk and ambiguous-subject cases are handled through retrieval
  before write
- the LLM emits structured graph update plans instead of Cypher
- the custom writer validates graph primitives before generating Cypher
- committed memory writes are saved idempotently under the active app user
- profiles can be reused across different thread IDs for the same app user
- one app user's updates do not mutate another app user's profile record
- message history remains isolated per thread
- tests cover same-app-user cross-thread profile reuse and update
- tests cover cross-user profile isolation
- tests cover duplicate-risk and ambiguous-subject conversations
- the optional identity-linking layer is explicitly designed or deferred
- Graphiti/Zep and automatic schema evolution remain outside Stage 5
