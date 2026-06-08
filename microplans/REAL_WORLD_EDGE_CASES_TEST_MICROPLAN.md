# Real-World Edge Cases Test Microplan

Scope: define the real-world scenario matrix that should drive the next wave of
tests for `src/graphv3.py` and the surrounding parent/create/update workflows.

This is not one final test file.

It is the prioritized source document for several future tests.

## Ordinary path

The ordinary expected path is:

1. one or more human messages enter the parent graph
2. `planner_node(...)` splits create and update work
3. create-side work extracts new profiles
4. update-side work fans out by existing `user_id`
5. committed results merge back into parent `existing`

## Main edge-case buckets

1. No-op outcomes
   - update branch is routed but no real field should change
   - low-signal message should do almost nothing
2. Repeated mentions
   - same new person appears across several messages
   - same existing person is refined by several messages in one batch
3. Mixed intent
   - one message contains both create and update information
   - one message mentions several people with different downstream actions
4. Runtime boundaries
   - wrapper nodes receive dict-shaped state instead of model-shaped state
   - routed branches behave differently from direct unit calls
5. Multi-turn accumulation
   - first turn creates a profile, later turn updates it
   - later turn corrects or contradicts an earlier fact
6. Repair and handoff
   - create mismatch reaches `human(...)`
   - update validation failure reaches `patch(...)` or `human_repair(...)`
7. Conservative versus risky decisions
   - planner chooses create instead of risky overwrite
   - planner wrongly maps a new person onto an existing profile
8. Shared evidence and merge-back
   - one shared message is relevant to several branches
   - several branch results merge back without losing data

## Second-pass additions

The first brainstorm was not broad enough without these:

- contradiction or self-correction across turns
- empty patch result inside a valid update branch
- low-drama combinations where one branch is real and another branch is a no-op
- indirect reference after a direct mention
- mixed boring outcomes, not only dramatic failures

## Highest-risk combinations

1. repeated new person + mixed create/update
2. no-op update + routed wrapper boundary
3. second turn + create-then-update
4. shared message + multi-user update fanout
5. contradiction + merge-back behavior
6. invalid candidate + update repair loop
7. human repair + wrong resume payload
8. indirect reference + conservative classification

## Priority matrix

### Priority 1: must test soon

1. update-only branch with an empty patch result
   - should not crash
   - should behave as a no-op update
2. first turn creates one profile, second turn updates that same profile
3. one shared message mentions:
   - one existing user
   - one new user
   and later messages refine both branches separately
4. one shared message updates two existing users at once
5. update repair path:
   - invalid candidate
   - retry through `patch(...)`
   - eventual success
6. `human_repair(...)` bad resume payload first, valid payload second
7. create mismatch path reaching `human(...)`

### Priority 2: strong next wave

1. repeated new person across three messages
2. contradiction for an existing user across turns
3. low-signal message that should do almost nothing
4. one message contains two new people with overlapping attributes
5. planner prefers create over risky overwrite in a maybe-match case
6. one batch has one real update branch and one no-op update branch

### Priority 3: later but important

1. indirect references after direct mentions
2. contradiction for a newly created person before the Part 3 refactor is done
3. mixed low-drama combinations across several turns
4. stronger ambiguity cases reserved for Part 4

## Tests this microplan should produce later

This document should lead to:

- one no-op update integration test
- one create-then-update multi-turn integration test
- one stronger mixed create+update integration test
- one shared-message multi-update integration test
- one create human-handoff integration test
- one update human-repair integration test
- one contradiction/self-correction test for existing users

## Important reminder

These scenarios are still not fully exhaustive.

What remains underexplored and should be discussed again with the human later:

- weird real user phrasings
- indirect references in natural language
- contradictory low-signal follow-ups
- combinations of two “boring” cases that become dangerous together
