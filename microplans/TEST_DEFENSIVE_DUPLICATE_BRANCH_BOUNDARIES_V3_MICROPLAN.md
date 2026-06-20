# Test Defensive Duplicate Branch Boundaries V3 Microplan

## Scope

Create `tests/test_defensive_duplicate_branch_boundaries_v3.py` after the
create-recovery migration tests are stable.

This file should define defensive behavior for parent-planning outputs that
could otherwise create several update branches for the same persisted profile
and make results depend on parallel completion order.

## Why This Is Separate From Recovery

Create and update recovery handle failures inside one branch.

Duplicate-boundary tests handle parent-planning outputs that accidentally
repeat the same existing `candidate_existing_id`.

Do not mix these concerns into Tests 5, 9, or 10 unless a duplicate case also
creates a unique recovery behavior not covered there.

## Chosen Policy

Freeze only the policy that is safe with the current architecture:

- duplicate existing buckets targeting the same `candidate_existing_id` are
  merged inside `subject_planner_node(...)`
- the merged bucket keeps the first label and combines message IDs in stable
  order without duplicates
- fanout receives one clean update bucket for that user ID

Do not freeze duplicate-new-label or mixed new/existing label policy here.
Those require the future persistence-backed identity-resolution architecture
described in `memory_agent.drawio.xml`.

## Required Tests

### 1. Duplicate Existing Update Targets Merge In Planner Output

Two existing-classified buckets target the same user id.

Assert `subject_planner_node(...)` returns one clean existing bucket whose
`message_ids` combine both duplicated buckets.

### 2. Merged Existing Target Produces One Update Branch

Run the parent graph with duplicated existing buckets returned by the fake
planner.

Assert only one update branch is called and its prompt contains all supporting
messages from the merged bucket.

### 3. Duplicate New Labels Are Deferred

Two new-classified buckets may share a label but still refer to different real
people.

Assert the current planner cleanup does not merge or reject duplicate new
labels. Future identity resolution should handle this with richer persistence
signals.

## Must Not Test Here

- normal create failure recovery
- normal update human repair
- parent happy-path create/update routing
- shared persistence across thread IDs

## Run Command

```bash
.venv/bin/pytest -q tests/test_defensive_duplicate_branch_boundaries_v3.py
```
