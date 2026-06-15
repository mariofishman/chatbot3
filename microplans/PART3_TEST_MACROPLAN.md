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

### 10. Create `tests/test_create_failure_policy_v3.py`

Coverage:

- extraction failure behavior
- invalid or missing structured extraction output
- whether create failure should stop, retry, interrupt, or preserve sibling
  branch results
- explicit create-side failure policy

Workflow:

- [ ] Microplan written
- [ ] Microplan reviewed
- [ ] Test file created
- [ ] Tests reviewed
- [ ] Focused file passed
- [ ] Full suite passed
- [ ] Completion recorded

### 11. Create `tests/test_defensive_duplicate_branch_boundaries_v3.py`

Coverage:

- duplicate subject buckets for one person
- several update branches targeting the same existing profile ID
- malformed or conflicting bucket combinations
- explicit defensive behavior where branch results could otherwise depend on
  completion order

Workflow:

- [ ] Microplan written
- [ ] Microplan reviewed
- [ ] Test file created
- [ ] Tests reviewed
- [ ] Focused file passed
- [ ] Full suite passed
- [ ] Completion recorded

## Completion Gate

Part 3 testing is complete when:

- [ ] All eleven workflows are complete
- [ ] Every focused test file passes
- [ ] The full suite passes
- [ ] Coverage is reviewed against
      `PART3_FANOUT_WRAPPER_INTEGRATION_EDGE_CASES.md`
- [ ] Remaining gaps are moved into an explicit future architectural plan
