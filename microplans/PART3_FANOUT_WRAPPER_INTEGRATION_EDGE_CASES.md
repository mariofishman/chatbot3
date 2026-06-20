# Part 3 Fanout, Wrapper, And Integration Edge Cases

This document is the scenario source for testing the completed Part 3
subject-bucket architecture.

It does not replace or modify:

- `UPSTREAM_SUBJECT_NODE_EDGE_CASES.md`
- `REAL_WORLD_EDGE_CASES_TEST_MICROPLAN.md`
- the older create, update, mixed-path, no-op, and multi-turn microplans

Those documents remain useful sources. This document translates their strongest
ideas into the current architecture, where:

- `SubjectBucketList` is the only parent routing plan
- one `SubjectBucket` represents one person
- one new bucket produces one create branch
- one existing bucket produces one update branch
- parallel branch results merge into parent `existing`

This is an ideation document, not a test implementation.

## Ordinary Path

The subject planner returns valid buckets. The parent router creates exactly one
branch per bucket. Each branch receives only its subject and supporting
messages. Create branches return one new profile; update branches return one
committed existing profile. The parent reducer merges every branch result
without losing unrelated profiles.

## Existing Ideas Carried Forward

The previous ideation remains directly relevant for:

- no-subject and low-signal messages
- one message supporting several people
- one person supported by several messages
- named and unnamed new people
- repeated mentions across messages and turns
- mixed existing and new people
- existing people mentioned without actionable updates
- corrections and contradictions
- shared-message fanout
- create-then-update across checkpointed turns
- runtime differences between direct function calls and routed workers
- merge-back behavior after parallel branches

## Edge-Case Buckets

### 1. Router Outcomes

1. No subjects.
   - Expected: route only to `END`.

2. One new subject.
   - Expected: one create `Send`.

3. One existing subject.
   - Expected: one update `Send`.

4. Several new subjects.
   - Expected: one create `Send` per subject.

5. Several existing subjects.
   - Expected: one update `Send` per subject.

6. Mixed new and existing subjects.
   - Expected: create and update `Send` objects coexist in one routing result.

7. Bucket order changes.
   - Expected: branch behavior and final merged profiles remain equivalent;
     tests should not rely on branch order unless the graph guarantees it.

### 2. Supporting-Message Filtering

8. One subject has one supporting message.
   - Expected: branch receives exactly that message.

9. One subject has several supporting messages.
   - Expected: one branch receives all listed messages, not one branch per
     message.

10. One message supports several subjects.
    - Expected: that message appears in every relevant branch.

11. Shared message plus subject-specific messages.
    - Expected: each branch receives the shared message and only its own
      additional messages.

12. State contains human, AI, and system messages.
    - Expected: branch receives only messages whose IDs are listed by its
      bucket, regardless of unrelated accumulated state.

13. Bucket message IDs are valid but listed in a different order from parent
    messages.
    - Current expected behavior: branch messages follow parent-state order.

14. Bucket repeats a valid message ID internally.
    - Current behavior: filtering parent messages prevents duplicate branch
      messages.

15. Bucket references an unknown message ID.
    - Normally prevented by `subject_planner_node`.
    - Direct fanout test should document whether the branch silently omits it
      or whether stronger defensive validation is desired later.

16. Subject planner returns duplicate buckets for the same new person while
    every referenced message ID is valid.
    - Current risk: fanout creates duplicate profiles because identifier
      validation cannot detect semantic duplication.

### 3. Create Fanout And Extraction

17. Named new subject with complete information.
    - Expected: one new profile.

18. Named new subject with partial information.
    - Expected: one profile with unknown fields left empty.

19. Unnamed new subject with a relationship label.
    - Expected: one profile based only on supporting facts; no invented name.

20. New subject supported by several messages.
    - Expected: extraction uses all supporting messages once.

21. Several new subjects share one message.
    - Expected: separate extraction branches, each constrained by its subject
      label.

22. Two new subjects have overlapping attributes.
    - Expected: separate profiles; branch context must not leak facts between
      subjects.

23. Extraction returns a profile whose name differs from the provisional
    subject label.
    - Expected: accept when supported by messages, such as an unnamed subject
      later becoming named.

24. Extraction returns sparse but valid structured output.
    - Expected: create branch completes and returns one profile.

25. Structured extraction raises or returns schema-invalid output.
    - Expected: extraction retries once for expected structured-output
      failures, then reaches one human create-repair interrupt if retry fails.
      Valid human submit commits; decline or invalid submit ends without
      creating.

26. Generated IDs from several create branches.
    - Expected: every created profile receives a distinct ID.

### 4. Update Fanout And Update Subgraph

27. Existing subject with one actionable update.
    - Expected: exactly one profile is updated.

28. Existing subject supported by several messages.
    - Expected: one update branch receives all supporting messages.

29. Existing subject is mentioned but has no actionable change.
    - Expected: update branch completes as a no-op and preserves the profile.

30. Several existing subjects share one message.
    - Expected: each update branch receives exactly one target profile and the
      shared message.

31. Shared message plus one subject-specific update.
    - Expected: no cross-profile field contamination.

32. One update succeeds while another is a no-op.
    - Expected: both profiles remain in final state; only one changes.

33. One update succeeds while another requires patch repair.
    - Expected: both branches complete within the parent superstep and both
      committed profiles survive merge-back.

34. One update reaches human repair.
    - Expected: the parent superstep pauses transactionally. With a
      checkpointer, completed sibling-task writes remain available as pending
      writes and are committed only after the interrupted work resumes and the
      superstep completes.
    - Important but may require a separate focused integration test.

35. Candidate existing ID is absent from parent `existing`.
    - Normally prevented by `subject_planner_node`.
    - Current fanout behavior would fail during profile lookup; document this
      as a defensive boundary rather than an ordinary path.

### 5. Wrapper And Runtime-State Boundaries

36. Direct wrapper call receives a dictionary-shaped branch payload.

37. Parent-routed wrapper receives the state shape produced by `Send`.

38. Create wrapper passes only `subject` and `messages` into
    `extract_subgraph`.

39. Update wrapper passes only one selected `existing` profile and supporting
    `messages` into `update_subgraph`.

40. Wrapper returns a partial parent-state update containing only `existing`.

41. Wrapper result is consumed by the parent reducer rather than replacing the
    entire parent state.

42. A direct unit test passes a model-shaped state while routed execution uses
    a different runtime shape.
    - Tests must exercise routed execution, not only direct calls.

43. Branch payload omits a required key.
    - Expected current behavior: fail clearly rather than silently processing
      the wrong subject or messages.

### 6. Parallel Merge-Back

44. Several create branches return new profiles.
    - Expected: every new profile survives merge-back.

45. Several update branches return different existing profile IDs.
    - Expected: every updated profile survives merge-back.

46. Mixed create and update branches return concurrently.
    - Expected: new and updated profiles coexist in final `existing`.

47. One update result replaces an existing profile while unrelated profiles
    remain unchanged.

48. One branch returns no effective field change.
    - Expected: it does not erase another branch's result.

49. Two branches return the same profile ID.
    - Not expected under one-bucket-per-person routing.
    - Test or document reducer overwrite behavior as a defensive boundary.

50. Branch completion order changes.
    - Expected: final result is equivalent when branch IDs are distinct.
    - Do not try to control or assert runtime completion order. Prove
      order-independence at the reducer boundary and prove that every routed
      branch result survives in parent integration.

### 7. Parent Integration And Multi-Turn State

51. Create-only parent run.

52. Update-only parent run.

53. Mixed create and update parent run.

54. One shared message mentions both a new and existing person.
    - Expected: same message reaches both branch types.

55. One shared message mentions several new and existing people.
    - Expected: one branch per subject and complete merge-back.

56. First turn creates one person; second turn updates that same committed ID.
    - Expected: no duplicate profile is created.

57. First turn creates several people; second turn updates only one.
    - Expected: all profiles remain, and only the selected one changes.

58. First turn creates a person from partial information; second turn adds new
    facts.
    - Expected: later subject classification selects the committed existing
      profile and update subgraph preserves prior facts.

59. Second turn contains only a no-subject message while checkpointed history
    still contains earlier people.
    - Expected according to current accumulated-history design: earlier people
      may be detected and routed again, producing safe no-op updates rather
      than duplicate creates.

60. Later turn corrects or contradicts an existing fact.
    - Expected: update behavior follows the latest supported information
      without duplicating the person.

61. Same thread versus different thread IDs.
    - Expected: same thread accumulates state; different threads remain
      isolated.

62. A later turn produces a different `SubjectBucketList` from the prior turn.
    - Expected: `subjects` is replaced by the latest planner output rather than
      accumulated like `messages`.

63. The planner returns two existing buckets with the same
    `candidate_existing_id`.
    - Expected: `subject_planner_node(...)` merges them into one clean existing
      bucket before fanout, preserving all supporting message IDs.

## Highest-Risk Combined Scenarios

1. One shared message mentions:
   - one existing person with an actionable update
   - one existing person with no new facts
   - one named new person
   - one unnamed related new person

2. One new person appears across three messages, one of which also updates an
   existing person.

3. Two existing people share one message; one update succeeds and the other is
   a no-op.

4. Mixed create/update fanout plus branch completion in a different order.

5. First turn creates two people from one message; second turn updates only one
   using an indirect reference.

6. Second checkpointed turn reanalyzes old messages plus a new correction,
   while preserving IDs and avoiding duplicate profiles.

7. Routed wrapper execution plus partial parent-state return plus parallel
   reducer merge.

8. Shared supporting message plus subject-specific messages plus overlapping
   profile attributes, testing branch isolation.

## Prioritized Scenario Matrix

| Priority | Scenario | Main Risk |
|---|---|---|
| Now | No subjects routes to `END` | Incorrect unnecessary branch |
| Now | One bucket produces exactly one branch | Broken unit-of-work contract |
| Now | One subject with several messages | Accidental branch-per-message behavior |
| Now | Shared message appears in several branches | Lost evidence during fanout |
| Now | Several new subjects | Lost or combined create branches |
| Now | Several existing subjects | Wrong target profile or lost update |
| Now | Existing subject with no actionable update | No-op update crash or mutation |
| Now | Mixed create and update batch | Original architecture defect remains |
| Now | Routed wrapper state shapes | Direct tests pass while graph execution fails |
| Now | Parallel create/update merge-back | Branch result lost by reducer |
| Now | Create then update on a later turn | Duplicate profile or stale classification |
| Now | Checkpointed second-turn accumulated history | Duplicate messages/profiles or repeated unsafe work |
| Now | Later-turn subjects replace earlier subjects | Stale routing buckets accumulate |
| Soon | Shared message plus subject-specific messages | Cross-branch evidence leakage |
| Soon | Several creates followed by one update | Unrelated profile loss |
| Soon | One successful update plus one repaired update | Parallel branch and retry interaction |
| Soon | Same thread versus different threads | State leakage across conversations |
| Now | Human repair during parallel parent fanout | Interrupt/checkpoint complexity |
| Now | Provider or structured-output failure on create | Failure-policy decision |
| Now | Duplicate existing planner buckets by candidate ID | Planner cleanup boundary |

## Tests To Build Now

The first test wave should cover:

1. focused create and update fanout contracts
2. focused wrapper contracts using routed payload shapes
3. no-subject routing
4. create-only parent integration
5. update-only parent integration, including no-op
6. mixed create/update parent integration with shared evidence
7. checkpointed create-then-update integration
8. merge-back from several parallel branches

These scenarios should be combined efficiently, but assertions must make each
contract failure easy to diagnose.

## Tests That Can Wait

- semantic identity-resolution cases reserved for Part 4
- exhaustive natural-language phrasing evaluation

## Coverage Check

- Input variation: covered by the earlier subject ideation and carried into
  integration combinations.
- Turn order and timing: covered.
- State accumulation: covered.
- Routing and fanout: covered.
- Wrapper boundaries: covered.
- Interrupt and resume: covered by focused create and update recovery tests,
  including parallel update repair.
- Runtime type and state shape: covered.
- No-op and partial outcomes: covered.
- Merge-back behavior: covered.
- Pairwise combinations: covered.

## Blind-Spot Attack

Failures that would be especially embarrassing if found manually first:

- a second turn crashes because routed state differs from a direct unit test
- one shared message reaches only one of several relevant subjects
- several parallel branches complete but only the last profile survives
- a no-op existing-person mention erases or mutates the profile
- a person created on turn one is duplicated instead of updated on turn two
- create and update paths work separately but fail when routed together
- accumulated history causes repeated creation of already committed people
- stale subject buckets survive into later turns and route obsolete work
- duplicate valid buckets fan out twice because only identifier validity was
  checked

## Decisions From Human Co-Ideation

- The first wave must prove both several subjects in one message and one
  subject accumulated across several messages or turns.
- The highest-risk mixed case is one shared message that supports new and
  existing people, combined with subject-specific messages.
- Repeated accumulated-history routing may currently produce a safe no-op
  update; suppressing that branch is a possible later optimization.
- Parallel update repair, create repair, and duplicate branch boundaries were
  promoted into focused deterministic tests after the first wave because they
  added checkpointer, interrupt, and reducer-order risk.

## Post-Audit Missing-Test Implementation Plan

This section was added after reviewing every test currently present in
`tests/`. It converts the earlier scenario ideation into an organized
implementation plan for all missing coverage.

This section is now the authoritative test-file roadmap for this document.
Earlier sections remain the scenario source, but their broad phrases such as
"tests to build now" should be interpreted through the concrete file plan
below.

The audit concluded:

- every current test file still protects relevant behavior
- stale update-state fixtures were repaired rather than deleted
- existing tests already cover subject-planner semantics, subject-bucket
  validation, reducers, helpers, and update-subgraph internals
- the missing coverage is concentrated at the new fanout, wrapper, parent
  integration, and complete multi-turn boundaries

### Test Harness Rules

Apply these rules to every new test file:

- use a fresh compiled graph and checkpointer for each checkpointed test
- use a unique thread ID per test so state cannot leak between cases
- make fake structured-output behavior select results by schema, prompt, or
  branch subject; never rely on concurrent branch invocation order
- distinguish direct wrapper contract tests from parent-routed integration
  tests; both boundaries are required
- do not assert parallel branch completion order because LangGraph does not
  guarantee it
- treat a parallel superstep as transactional: sibling task writes are not
  merged into completed parent state until the superstep completes
- when testing simultaneous interrupts, resume using interrupt IDs rather than
  assuming one positional resume value

### Existing Files To Extend

#### `tests/test_upstream_subject_node_v3.py`

Add:

- later checkpointed planner output replaces prior `subjects` rather than
  accumulating them
- one no-subject second turn with accumulated history

Do not duplicate the subject-detection scenarios already covered by this file.
Duplicate semantic-bucket policy remains deferred.

#### `tests/test_state_reducers_v3.py`

Add:

- merge several create branch slices
- merge mixed create and update slices in different orders when IDs are
  distinct
- document same-ID overwrite behavior when two branch slices collide

These tests isolate reducer semantics. Parent integration tests must still
prove that routed branch outputs actually reach the reducer.

#### `tests/test_update_subgraph_integration_v3.py`

Add:

- empty `PatchProposalList` completes as a no-op update

The existing retry-and-commit test already covers update repair. Do not repeat
all internal update-node unit tests here.

### New Files Required For The First Test Wave

#### 1. `tests/test_subject_fanout_v3.py`

Scope:

- `fan_out_creates(...)`
- `fan_out_updates(...)`
- `route_after_subject_planner(...)`

Required tests:

1. no subjects routes only to `END`
2. one new bucket produces exactly one create branch
3. one existing bucket produces exactly one update branch containing exactly
   one selected existing profile
4. one subject supported by several messages still produces one branch
5. several new buckets produce one create branch each
6. several existing buckets produce one update branch each
7. mixed new and existing buckets coexist in one routing result
8. one shared message appears in every relevant branch
9. shared message plus subject-specific messages filters correctly
10. unrelated parent messages do not enter a branch
11. branch message order follows parent-state message order

This file covers ordinary and first-wave routing/fanout cases. Unknown
supporting-message IDs, repeated message IDs, missing existing candidate IDs,
and duplicate semantic buckets remain deferred defensive boundaries so the
first wave does not freeze an accidental policy.

#### 2. `tests/test_extract_branch_v3.py`

Scope:

- `extract_node(...)`
- compiled `extract_subgraph`
- `run_extract_subgagent(...)`

Required tests:

1. named new subject produces exactly one profile
2. partial information produces one sparse valid profile
3. unnamed relationship-labeled subject does not invent a name
4. several supporting messages reach the extraction prompt once each
5. subject label constrains extraction when a shared message mentions several
   people
6. wrapper passes only `subject` and supporting `messages` into the subgraph
7. wrapper returns only the partial parent `existing` update
8. routed branch payload shape works, not only a handcrafted direct-node state
9. missing required branch state fails clearly

Do not recreate the removed batch-extraction or create-side human-repair tests;
those behaviors are no longer part of the architecture. Distinct IDs across
parallel extraction branches belong in the parent integration file.

#### 3. `tests/test_update_parent_branch_v3.py`

Scope:

- routed update `Send` payload
- `run_update_subgagent(...)`
- real compiled `update_subgraph`
- parent-compatible partial result

Required tests:

1. routed payload with one selected profile and one message completes
2. several supporting messages reach one update branch
3. wrapper passes only one existing profile and supporting messages into the
   update subgraph
4. wrapper returns only the partial parent `existing` update
5. existing-person mention with no actionable update completes unchanged
6. missing required branch payload fails clearly

This file complements, rather than duplicates, the internal update-subgraph
unit and integration tests. Shared-message fanout and multi-branch merge-back
belong in fanout and parent integration tests.

#### 4. `tests/test_parent_subject_routing_integration_v3.py`

Scope:

- complete single-run parent graph
- subject planner output
- create/update fanout
- wrappers and subgraphs
- parallel merge-back

Required tests:

1. no detected subjects completes without create or update branches
2. create-only batch
3. update-only batch
4. mixed create and update batch
5. one shared message mentions one new and one existing person
6. one shared message mentions several new and existing people
7. repeated new subject across several messages remains one create branch
8. shared messages and subject-specific messages remain isolated correctly
9. several create branches all survive merge-back
10. several update branches all survive merge-back
11. mixed create/update branch outputs coexist in final `existing`
12. one real update plus one no-op update preserves both profiles
13. several extraction branches generate distinct profile IDs

Use deterministic fake structured outputs. This file must exercise the
compiled parent graph rather than manually calling every function in sequence.
It must assert that all distinct-ID branch results survive, but it must not
attempt to control or assert scheduler completion order.

#### 5. `tests/test_parent_multiturn_integration_v3.py`

Scope:

- compiled parent graph with checkpointer
- realistic repeated invocations
- accumulated messages, subjects, and existing profiles

Required tests:

1. first turn creates one profile; second turn updates that same committed ID
   without duplication
2. first turn creates several profiles; second turn updates only one while
   preserving the others
3. first turn creates a sparse profile; second turn adds facts without losing
   prior fields
4. later correction updates the same profile rather than creating another
5. second-turn accumulated history contains each message once
6. a second planner output containing no subjects replaces earlier buckets,
   routes no new branches, and preserves committed profiles
7. same thread accumulates state while different thread IDs remain isolated

This file covers the failures most likely to appear only during real terminal
use.

### Deferred New Files

These files should be created only after the first test wave passes and their
failure policies are confirmed.

#### `tests/test_parallel_update_repair_integration_v3.py`

Potential coverage:

- one parallel update succeeds while another uses model repair
- one parallel update succeeds while another reaches `human_repair`
- a paused parallel superstep does not expose a partially merged parent state
- completed sibling-task writes persist as pending writes with a checkpointer
- simultaneous interrupts resume through an interrupt-ID-to-value map
- resumed completion merges every successful and repaired branch result

Reason deferred:

- combines parallel fanout, retry, checkpointer, and interrupt semantics
- deserves a focused design rather than being hidden inside the main parent
  integration file

#### `tests/test_create_failure_policy_v3.py`

Potential coverage:

- structured extraction provider failure
- schema-invalid create output
- missing or unusable extraction result
- one create branch fails while sibling create or update branches succeed
- a failed parallel superstep does not partially merge sibling outputs into
  completed parent state

Reason deferred:

- current create-side failure policy intentionally propagates exceptions
- test only after deciding whether propagation and transactional failure are
  the desired stable contracts

#### `tests/test_defensive_duplicate_branch_boundaries_v3.py`

Potential coverage:

- duplicate existing buckets target the same persisted profile ID
- planner cleanup merges those buckets before fanout
- the single update branch receives all supporting messages
- duplicate new-person labels remain unchanged for now

Reason deferred:

- duplicate new-label and mixed new/existing ambiguity require richer
  persistence-backed identity resolution from the future memory-agent design
- the current safe policy only freezes behavior for duplicate
  `candidate_existing_id` values, because that ID uniquely identifies the
  persisted profile

### Coverage Mapping After This Plan

The current suite plus the files above cover every scenario category in this
document:

- subject detection and input variation:
  `test_upstream_subject_node_v3.py`
- subject schema boundaries:
  `test_subject_bucket_v3.py`
- focused create/update fanout and routing:
  `test_subject_fanout_v3.py`
- create wrapper and extraction:
  `test_extract_branch_v3.py`
- update wrapper and routed update behavior:
  `test_update_parent_branch_v3.py`
- update internals and repair:
  existing update-side unit/integration tests
- merge semantics:
  `test_state_reducers_v3.py`
- complete single-run parent behavior:
  `test_parent_subject_routing_integration_v3.py`
- complete checkpointed multi-turn behavior:
  `test_parent_multiturn_integration_v3.py`
- parallel repair, create failure policy, and duplicate defensive boundaries:
  deferred focused files

### Test Implementation Order

Build in this order:

1. extend the three existing files listed above
2. create `test_subject_fanout_v3.py`
3. create `test_extract_branch_v3.py`
4. create `test_update_parent_branch_v3.py`
5. create `test_parent_subject_routing_integration_v3.py`
6. create `test_parent_multiturn_integration_v3.py`
7. review first-wave coverage against this document
8. decide whether to build the deferred files

This order moves from deterministic contracts toward increasingly integrated
and stateful behavior, making failures easier to localize.
