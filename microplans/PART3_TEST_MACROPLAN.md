# Part 3 Test MacroPlan

## Purpose

This MacroPlan is the authoritative progress tracker for building the missing
Part 3 tests one file at a time.

Coverage requirements come from:

- `microplans/PART3_FANOUT_WRAPPER_INTEGRATION_EDGE_CASES.md`

That edge-case document explains what must be covered. This MacroPlan defines
the order of execution and tracks each test file through the complete
microplan-to-testing workflow.

`microplans/SUITE_TESTS.md` describes an older architecture and must not
override this MacroPlan or the Part 3 edge-case document.

## Execution Rule

Complete one file before starting the next file.

Every file must pass this workflow:

1. Write a file-specific microplan from the relevant edge-case requirements.
2. Review and improve the microplan with `md-file-review`.
3. Confirm that the microplan does not duplicate coverage assigned elsewhere.
4. Implement or extend the test file with `microplan-test-builder`.
5. Review the implemented tests against the approved microplan and production
   architecture.
6. Run the focused test file.
7. Fix failures and rerun the focused test file until it passes.
8. Run the full existing test suite.
9. Fix regressions and rerun both the focused file and full suite.
10. Record completion here before advancing.

Do not create several test files before running them. A focused failure must be
understood while its change is still isolated.

## Rules For Every Test File

- Use a fresh compiled graph and checkpointer for each checkpointed test.
- Use a unique thread ID per test.
- Do not rely on concurrent branch invocation or completion order.
- Route fake structured outputs by schema, prompt, or branch subject.
- Keep direct contract tests distinct from compiled-graph integration tests.
- Test partial state returns through real graph execution where assigned.
- Do not freeze undecided defensive-boundary behavior in first-wave tests.
- Do not advance while the focused file or full suite is failing.

## First-Wave Execution Order

### 1. Extend `tests/test_upstream_subject_node_v3.py`

Coverage:

- later checkpointed planner output replaces prior `subjects`
- no-subject second turn with accumulated history

Workflow:

- [x] Microplan written:
      `microplans/TEST_UPSTREAM_SUBJECT_NODE_V3_EXTENSION_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file extended
- [x] Tests reviewed
- [x] Focused file passed: `21 passed`
- [x] Full suite passed: `63 passed`
- [x] Completion recorded

### 2. Extend `tests/test_state_reducers_v3.py`

Coverage:

- merge several create branch slices
- merge mixed create and update slices in different orders for distinct IDs
- document same-ID whole-profile overwrite behavior

Workflow:

- [x] Microplan written:
      `microplans/TEST_STATE_REDUCERS_V3_EXTENSION_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file extended
- [x] Tests reviewed
- [x] Focused file passed: `8 passed`
- [x] Full suite passed: `66 passed`
- [x] Completion recorded

### 3. Extend `tests/test_update_subgraph_integration_v3.py`

Coverage:

- empty `PatchProposalList` completes as a no-op update

Workflow:

- [x] Microplan written:
      `microplans/TEST_UPDATE_SUBGRAPH_NOOP_EXTENSION_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file extended
- [x] Tests reviewed
- [x] Focused file passed: `2 passed`
- [x] Full suite passed: `67 passed`
- [x] Completion recorded

### 4. Create `tests/test_subject_fanout_v3.py`

Coverage:

- no-subject routing
- one branch per new or existing subject
- several create and update branches
- mixed create/update routing
- one subject supported by several messages
- shared and subject-specific message filtering
- unrelated-message exclusion
- parent message-order preservation

Workflow:

- [x] Microplan written:
      `microplans/TEST_SUBJECT_FANOUT_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed: `6 passed`
- [x] Full suite passed: `73 passed`
- [x] Completion recorded

### 5. Create `tests/test_extract_branch_v3.py`

Coverage:

- named, sparse, and unnamed new-subject extraction
- several supporting messages used once each
- subject label constrains shared-message extraction
- extract wrapper input and partial parent-state output contracts
- real routed branch payload shape
- missing required branch state fails clearly

Workflow:

- [x] Microplan written:
      `microplans/TEST_EXTRACT_BRANCH_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed: `7 passed`
- [x] Full suite passed: `80 passed`
- [x] Completion recorded

### 6. Create `tests/test_update_parent_branch_v3.py`

Coverage:

- routed one-profile update payload
- several supporting messages in one update branch
- update wrapper input and partial parent-state output contracts
- no-op update remains unchanged
- missing required branch state fails clearly

Workflow:

- [x] Microplan written:
      `microplans/TEST_UPDATE_PARENT_BRANCH_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed: `4 passed`
- [x] Full suite passed: `84 passed`
- [x] Completion recorded

### 7. Create `tests/test_parent_subject_routing_integration_v3.py`

Coverage:

- complete no-subject, create-only, update-only, and mixed parent runs
- shared messages across new and existing people
- several create and update branches
- branch isolation
- parallel merge-back
- real update plus no-op update
- distinct IDs across extraction branches

Workflow:

- [x] Microplan written:
      `microplans/TEST_PARENT_SUBJECT_ROUTING_INTEGRATION_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed: `4 passed`
- [x] Full suite passed: `88 passed`
- [x] Completion recorded

### 8. Create `tests/test_parent_multiturn_integration_v3.py`

Coverage:

- create then update without duplication
- several profiles followed by one selected update
- sparse profile enriched later
- later correction updates the same profile
- accumulated messages remain unique
- no-subject output replaces prior buckets without losing profiles
- same-thread accumulation and cross-thread isolation

Workflow:

- [x] Microplan written:
      `microplans/TEST_PARENT_MULTITURN_INTEGRATION_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed: `4 passed`
- [x] Full suite passed: `92 passed`
- [x] Completion recorded

### 9. Create `tests/test_parallel_update_repair_integration_v3.py`

Coverage:

- one parallel update succeeds while another uses model repair
- one parallel update succeeds while another reaches `human_repair`
- several parallel updates reach `human_repair` and resume one at a time by
  interrupt ID
- a paused parallel superstep preserves completed sibling output while leaving
  the interrupted profile unchanged
- resumed repair completes without losing successful sibling updates

Workflow:

- [x] Microplan written:
      `microplans/TEST_PARALLEL_UPDATE_REPAIR_INTEGRATION_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed: `3 passed`
- [x] Full suite passed: `95 passed`
- [x] Completion recorded

## Create-Recovery Migration Review

This section records the second pass through the Part 3 tests after the
create- and update-recovery migration described in:

- `SHORT_TERM_PLANS/SHORT_TERM_PLAN3v5.md`

The original Test 1-9 completion records above remain as historical progress.
The checklist below records the focused migration-review pass and the added
Test 10 and Test 11 workflows.

### Production Migration

- [x] Complete create-recovery Steps 1–7 of `SHORT_TERM_PLAN3v5.md`
- [x] Complete update-parity Steps 8–10 of `SHORT_TERM_PLAN3v5.md`
- [x] Review the completed create- and update-recovery implementations
- [x] Confirm extraction UUID generation occurs only at the commit boundary
- [x] Confirm update automated retry, validation, and commit behavior remains
      unchanged before human escalation
- [x] Confirm create and update human repair each interrupt once and use
      explicit submit/decline envelopes

### Recovery-Test Adaptation Order

These workflows were completed one at a time. For each item, the listed
microplan was reviewed, the target test file was adapted or created, the
focused file was run, and the full suite was run before moving to the next
item.

1. `microplans/TEST_HUMAN_REPAIR_V3_ACTION_ENVELOPE_EXTENSION_MICROPLAN.md`
   -> `tests/test_human_repair_v3.py`
2. `microplans/TEST_UPDATE_SUBGRAPH_V3_UPDATE_RECOVERY_EXTENSION_MICROPLAN.md`
   -> `tests/test_update_subgraph_integration_v3.py`
3. `microplans/TEST_PARALLEL_UPDATE_REPAIR_V3_ACTION_ENVELOPE_EXTENSION_MICROPLAN.md`
   -> `tests/test_parallel_update_repair_integration_v3.py`
4. `microplans/TEST_EXTRACT_BRANCH_V3_CREATE_RECOVERY_EXTENSION_MICROPLAN.md`
   -> `tests/test_extract_branch_v3.py`
5. `microplans/TEST_CREATE_FAILURE_POLICY_V3_MICROPLAN.md`
   -> `tests/test_create_failure_policy_v3.py`
6. `microplans/TEST_UPDATE_PARENT_BRANCH_V3_DECLINE_COMPATIBILITY_MICROPLAN.md`
   -> `tests/test_update_parent_branch_v3.py`
7. `microplans/TEST_PARENT_SUBJECT_ROUTING_V3_RECOVERY_COMPATIBILITY_MICROPLAN.md`
   -> `tests/test_parent_subject_routing_integration_v3.py`
8. `microplans/TEST_PARENT_MULTITURN_V3_RECOVERY_COMPATIBILITY_MICROPLAN.md`
   -> `tests/test_parent_multiturn_integration_v3.py`
9. `microplans/TEST_DEFENSIVE_DUPLICATE_BRANCH_BOUNDARIES_V3_MICROPLAN.md`
   -> `tests/test_defensive_duplicate_branch_boundaries_v3.py`

### Tests Requiring Extension Microplans And Adaptation

#### Test 3: `tests/test_update_subgraph_integration_v3.py`

- [x] Write an update-human-repair compatibility extension microplan:
      `microplans/TEST_UPDATE_SUBGRAPH_V3_UPDATE_RECOVERY_EXTENSION_MICROPLAN.md`
- [x] Review the update-human-repair compatibility extension microplan
- [x] Preserve successful and no-op update behavior
- [x] Confirm valid submitted human patches continue to commit
- [x] Confirm declined or invalid human responses end without changing the
      existing profile
- [x] Run the focused file and record the result:
      `.venv/bin/pytest -q tests/test_update_subgraph_integration_v3.py` -> `7 passed`

#### Test 5: `tests/test_extract_branch_v3.py`

- [x] Write a create-recovery extension microplan:
      `microplans/TEST_EXTRACT_BRANCH_V3_CREATE_RECOVERY_EXTENSION_MICROPLAN.md`
- [x] Review the create-recovery extension microplan
- [x] Adapt direct `extract_node(...)` assertions to the candidate/error
      contract
- [x] Add model-retry, one-time human-repair, invalid-or-declined-human-input,
      and commit-boundary coverage
- [x] Preserve existing happy-path, sparse-profile, prompt, payload, and wrapper
      coverage
- [x] Run the focused file and record the result:
      `.venv/bin/pytest -q tests/test_extract_branch_v3.py` -> `24 passed`

#### Test 6: `tests/test_update_parent_branch_v3.py`

- [x] Write a decline-compatibility extension microplan:
      `microplans/TEST_UPDATE_PARENT_BRANCH_V3_DECLINE_COMPATIBILITY_MICROPLAN.md`
- [x] Review the decline-compatibility extension microplan
- [x] Add the focused declined-update wrapper compatibility case if still
      useful after lower-level update tests pass
- [x] Preserve routed payload, no-op update, wrapper contract, and missing-state
      coverage
- [x] Run the focused file and record the result:
      `.venv/bin/pytest -q tests/test_update_parent_branch_v3.py` -> `5 passed`

#### Test 7: `tests/test_parent_subject_routing_integration_v3.py`

- [x] Write a create-recovery compatibility extension microplan:
      `microplans/TEST_PARENT_SUBJECT_ROUTING_V3_RECOVERY_COMPATIBILITY_MICROPLAN.md`
- [x] Review the create-recovery compatibility extension microplan
- [x] Adapt deterministic fakes only where the additional extraction lifecycle
      requires it
- [x] Confirm no-subject, create-only, update-only, mixed, branch-isolation,
      and merge-back behavior remains intact
- [x] Avoid duplicating detailed create-repair coverage assigned to Test 10
- [x] Run the focused file and record the result:
      `.venv/bin/pytest -q tests/test_parent_subject_routing_integration_v3.py` -> `4 passed`

#### Test 8: `tests/test_parent_multiturn_integration_v3.py`

- [x] Write a create-recovery compatibility extension microplan:
      `microplans/TEST_PARENT_MULTITURN_V3_RECOVERY_COMPATIBILITY_MICROPLAN.md`
- [x] Review the create-recovery compatibility extension microplan
- [x] Adapt deterministic fakes only where required
- [x] Confirm committed create IDs remain usable by later update turns
- [x] Confirm temporary create candidates and errors do not leak into parent
      checkpointed state
- [x] Preserve all existing multi-turn and thread-isolation coverage
- [x] Run the focused file and record the result:
      `.venv/bin/pytest -q tests/test_parent_multiturn_integration_v3.py` -> `4 passed`

#### Test 9: `tests/test_parallel_update_repair_integration_v3.py`

- [x] Write a one-time update-human-repair extension microplan:
      `microplans/TEST_PARALLEL_UPDATE_REPAIR_V3_ACTION_ENVELOPE_EXTENSION_MICROPLAN.md`
- [x] Review the one-time update-human-repair extension microplan
- [x] Adapt valid human repair resumes to the submit action envelope
- [x] Add one declined update alongside successful siblings
- [x] Add mixed submit/decline responses across several parallel interrupts
- [x] Confirm declined profiles remain unchanged and no response interrupts
      again
- [x] Run the focused file and record the result:
      `.venv/bin/pytest -q tests/test_parallel_update_repair_integration_v3.py` -> `5 passed`

#### Focused Update Test: `tests/test_human_repair_v3.py`

- [x] Write a one-time action-envelope extension microplan:
      `microplans/TEST_HUMAN_REPAIR_V3_ACTION_ENVELOPE_EXTENSION_MICROPLAN.md`
- [x] Review the one-time action-envelope extension microplan
- [x] Replace repeated-interrupt expectations with submit, decline, malformed,
      missing-action, wrong-target, and invalid-patches outcomes
- [x] Add direct post-human router coverage
- [x] Run the focused file and record the result:
      `.venv/bin/pytest -q tests/test_human_repair_v3.py` -> `14 passed`

### Tests Expected To Remain Unchanged

- [x] Test 1: run `tests/test_upstream_subject_node_v3.py`
- [x] Test 2: review and run `tests/test_state_reducers_v3.py`; confirm only
      committed profiles reach the reducer
- [x] Test 4: review and run `tests/test_subject_fanout_v3.py`; confirm routed
      create payloads remain unchanged
- [x] Run `tests/test_route_patches_v3.py`
- [x] Run `tests/test_patch_v3.py`
- [x] Run `tests/test_validate_v3.py`
- [x] Run `tests/test_commit_v3.py`

Focused unchanged-set result:

```text
.venv/bin/pytest -q tests/test_upstream_subject_node_v3.py tests/test_state_reducers_v3.py tests/test_subject_fanout_v3.py tests/test_route_patches_v3.py tests/test_patch_v3.py tests/test_validate_v3.py tests/test_commit_v3.py
48 passed
```

### Migration Review Completion

- [x] All affected focused files pass
- [x] All unchanged focused files pass
- [x] The current full suite passes
- [x] New focused and full-suite results are recorded without erasing the
      original Test 1-9 completion history
- [x] Test 10 and Test 11 are completed against the implemented recovery and
      duplicate-existing-ID policies

Full-suite status after the final recovery-test adaptation:

```text
.venv/bin/pytest -q
145 passed
```

Completed affected queue items:

- `tests/test_human_repair_v3.py`
- `tests/test_update_subgraph_integration_v3.py`
- `tests/test_parallel_update_repair_integration_v3.py`
- `tests/test_extract_branch_v3.py`
- `tests/test_create_failure_policy_v3.py`
- `tests/test_update_parent_branch_v3.py`
- `tests/test_parent_subject_routing_integration_v3.py`
- `tests/test_parent_multiturn_integration_v3.py`
- `tests/test_defensive_duplicate_branch_boundaries_v3.py`

### 10. Create `tests/test_create_failure_policy_v3.py`

This workflow is part of the recovery-test adaptation queue above. Use
`microplans/TEST_CREATE_FAILURE_POLICY_V3_MICROPLAN.md` as the microplan.

Coverage:

- extraction failure behavior
- invalid or missing structured extraction output
- whether create failure should stop, retry, interrupt, or preserve sibling
  branch results
- explicit create-side failure policy

Workflow:

- [x] Microplan written:
      `microplans/TEST_CREATE_FAILURE_POLICY_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed:
      `.venv/bin/pytest -q tests/test_create_failure_policy_v3.py` -> `13 passed`
- [x] Full suite passed:
      `.venv/bin/pytest -q` -> `141 passed`
- [x] Completion recorded

### 11. Create `tests/test_defensive_duplicate_branch_boundaries_v3.py`

This workflow is part of the recovery-test adaptation queue above. Use
`microplans/TEST_DEFENSIVE_DUPLICATE_BRANCH_BOUNDARIES_V3_MICROPLAN.md` as the
microplan.

Coverage:

- duplicate existing-classified buckets targeting one persisted profile ID
- planner cleanup that merges duplicated `candidate_existing_id` buckets before
  fanout
- one resulting update branch that receives all supporting messages for the
  merged existing subject
- explicit deferral of duplicate-new-label policy until richer identity
  resolution and persistence exist

Workflow:

- [x] Microplan written:
      `microplans/TEST_DEFENSIVE_DUPLICATE_BRANCH_BOUNDARIES_V3_MICROPLAN.md`
- [x] Microplan reviewed
- [x] Test file created
- [x] Tests reviewed
- [x] Focused file passed:
      `.venv/bin/pytest -q tests/test_defensive_duplicate_branch_boundaries_v3.py` -> `3 passed`
- [x] Full suite passed:
      `.venv/bin/pytest -q` -> `145 passed`
- [x] Completion recorded

## Completion Gate

Part 3 testing is complete when:

- [x] All eleven workflows are complete
- [x] Every focused test file passes
- [x] The full suite passes
- [x] Coverage is reviewed against
      `PART3_FANOUT_WRAPPER_INTEGRATION_EDGE_CASES.md`
- [x] Remaining gaps are moved into an explicit future architectural plan
