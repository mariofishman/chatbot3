# SHORT_TERM_PLAN3v5

## Purpose

This is the executable roadmap for adding deliberate failure recovery to the
new-subject extraction branch before continuing Test 10 of
`microplans/PART3_TEST_MACROPLAN.md`.

The subject-planning, create fanout, update fanout, wrappers, and parent routing
completed in Part 3 remain in place. This plan changes only what happens inside
each create branch after one new `SubjectBucket` and its supporting messages
reach `extract_subgraph`.

## Problem

The current create branch performs one structured `UserProfile` extraction and
immediately commits it under a generated UUID.

If extraction fails, the exception stops the branch. The create branch has no
deliberate model retry, human-repair interrupt, or separate commit boundary.
Test 10 cannot freeze a useful create-failure policy until that behavior is
defined and implemented.

## Chosen Create-Recovery Contract

Each extraction branch processes exactly one new subject.

1. `extract_node(...)` attempts structured extraction once.
2. If the expected extraction or schema-validation operation fails,
   `extract_node(...)` invokes the model once more with a retry prompt that
   includes the latest error and the original subject-specific context.
3. A valid first or second result becomes `state.candidate`.
4. If the second attempt also fails, the branch records the latest expected
   extraction errors and routes to `human_create_repair(...)`.
5. The human supplies one complete valid `UserProfile`, not JSON patches.
6. `commit_created_profile(...)` generates the UUID and returns the committed
   profile through `state.existing`.

There is no automated extraction graph loop and no `attempts` field. The only
loop is local input validation inside `human_create_repair(...)`, allowing an
invalid human response to be corrected. Unexpected programming or
infrastructure errors must still propagate rather than being misrepresented as
repairable profile-validation errors.

## Desired State Contract

Refactor `ExtractAgentState` to carry:

- `subject`: the one new `SubjectBucket` assigned to this branch
- `messages`: only that subject's supporting messages
- `candidate: UserProfile | None`: a valid extracted or human-repaired profile
- `errors: list[str]`: the latest expected extraction or validation errors
- `existing`: populated only by `commit_created_profile(...)`

Important invariants:

- a valid sparse `UserProfile` is a successful candidate
- an extraction attempt must never generate or commit a UUID
- `errors` must be empty whenever a valid candidate is routed to commit
- `existing` must remain empty until commit
- only the latest expected extraction failure is presented to the human

## Desired Extract Subgraph

```text
START -> extract_node -> route_extraction
                           | valid candidate -> commit_created_profile -> END
                           | errors -> human_create_repair
                                      | valid human profile -> commit_created_profile -> END
                                      | invalid human profile -> interrupt again
```

## Execution Roadmap

Complete each step before starting the next.

### Step 1: Define The Recoverable Error Boundary

Before coding, inspect the structured-output call and identify the expected
provider, parsing, and `UserProfile` validation failures that belong in
`state.errors`.

Document that boundary beside the implementation:

- expected extraction/schema failures receive one model retry and then human
  repair
- missing, `None`, or otherwise unusable structured output is treated as an
  expected extraction failure rather than as an empty successful candidate
- invalid human repair input interrupts again with validation feedback
- unrelated programming and infrastructure failures propagate

This prevents a broad `except Exception` from hiding real defects.

### Step 2: Refactor `ExtractAgentState`

Add `candidate` and `errors`.

Keep `subject`, `messages`, and `existing`. Do not add `attempts`.

Verify that a create branch can hold an uncommitted candidate without exposing
it through the parent state's `existing` reducer.

### Step 3: Refactor `extract_node(...)`

Keep the current one-subject extraction prompt and supporting-message
filtering.

Add exactly one in-node retry for expected extraction failures:

- first call uses the normal extraction prompt
- second call uses a retry prompt containing the original task and latest error
- success returns `candidate` and clears `errors`
- missing or unusable output follows the same retry/error path as invalid
  structured output
- second expected failure returns no candidate and records the latest errors

Do not generate a UUID or return `existing` from this node.

### Step 4: Add `route_extraction(...)`

Route a valid candidate to `commit_created_profile`.

Route recorded expected extraction errors to `human_create_repair`.

Fail clearly if state violates the contract by containing neither a candidate
nor errors, or both simultaneously.

### Step 5: Add `human_create_repair(...)`

Interrupt with a concise payload containing:

- the subject label
- a formatted, serializable representation of the supporting messages
- the latest extraction errors
- instructions to provide one complete `UserProfile`

Validate the resumed value as a `UserProfile`.

- valid input becomes `candidate` and clears `errors`
- invalid input interrupts again with useful validation feedback

Do not ask the human for JSON patches and do not generate a UUID here.
Because LangGraph re-executes an interrupted node from its beginning, keep all
work before `interrupt(...)` free of non-idempotent side effects. The local
human-input validation loop is not an automated model-extraction retry loop.

### Step 6: Add `commit_created_profile(...)`

Require one valid candidate and no errors.

Generate one UUID only at this boundary and return:

```python
{"existing": {generated_id: candidate}}
```

The parent `merge_profiles` reducer remains responsible for merging committed
create and update branch slices.

### Step 7: Rewire And Review The Create Path

Rebuild `extract_subgraph` with the new nodes and conditional route.

Review `run_extract_subgagent(...)`, `fan_out_creates(...)`, and
`route_after_subject_planner(...)` without changing their established parent
contracts:

- one new bucket creates one extraction branch
- the wrapper passes one subject and its supporting messages
- the wrapper returns only the committed partial parent `existing` update
- create and update branches may still run in parallel

### Step 8: Review Every Part 3 Macroplan Test

Review all eleven workflows below before completing Test 10. Preserve relevant
existing assertions and change only tests whose contracts are affected.

Before editing any previously completed test file, write and review a narrow
extension microplan for that file. Record the new focused and full-suite
results without erasing its earlier completion history.

#### Test 1: `tests/test_upstream_subject_node_v3.py`

Expected action: run unchanged.

Reason: subject detection and classification happen before extraction recovery.

#### Test 2: `tests/test_state_reducers_v3.py`

Expected action: review and run unchanged.

Reason: the reducer still receives only fully committed profile dictionaries.
Confirm that candidates never reach this reducer before commit.

#### Test 3: `tests/test_update_subgraph_integration_v3.py`

Expected action: run unchanged.

Reason: create recovery must not alter update-subgraph behavior.

#### Test 4: `tests/test_subject_fanout_v3.py`

Expected action: review and run unchanged.

Reason: `fan_out_creates(...)` must continue sending one subject and its
supporting messages; recovery is internal to the extract subgraph.

#### Test 5: `tests/test_extract_branch_v3.py`

Expected action: substantially extend and adapt.

Preserve current happy-path coverage, then cover:

- valid first extraction commits once
- valid sparse first extraction commits without retry
- first expected failure followed by successful model retry
- two expected failures route to human repair
- valid human repair commits once
- invalid human repair input interrupts again
- UUID is absent before commit and generated only after a valid candidate
- wrapper still returns only committed partial parent `existing`

Direct `extract_node(...)` tests must stop expecting immediate `existing`
output and instead assert the candidate/error contract.

#### Test 6: `tests/test_update_parent_branch_v3.py`

Expected action: run unchanged.

Reason: the update wrapper and update subgraph are outside this refactor.

#### Test 7: `tests/test_parent_subject_routing_integration_v3.py`

Expected action: review and adapt its deterministic fake only as needed for the
additional extraction calls.

Preserve all no-subject, create-only, update-only, and mixed happy paths.
Confirm that successful create branches still merge with successful update
branches. Do not duplicate detailed create-repair coverage assigned to Test 10.

#### Test 8: `tests/test_parent_multiturn_integration_v3.py`

Expected action: review and adapt its deterministic fake only as needed.

Preserve all existing multi-turn behavior. Confirm that committed create IDs
remain stable for later updates and that temporary create candidates/errors do
not leak into parent checkpointed state.

#### Test 9: `tests/test_parallel_update_repair_integration_v3.py`

Expected action: run unchanged.

Reason: this is update-only coverage. Reuse its interrupt-ID and one-at-a-time
resume patterns when designing parallel create-repair tests.

#### Test 10: `tests/test_create_failure_policy_v3.py`

Expected action: replace the stale fail-fast microplan, then create the test
file around the new policy.

Required integration coverage:

- first extraction succeeds without retry or interrupt
- first extraction fails and second model attempt succeeds
- both model attempts fail and produce one human interrupt
- valid human response resumes and commits
- invalid human response interrupts again
- one create branch needs human repair while successful create/update siblings
  remain preserved as pending sibling work
- several create branches interrupt and resume one at a time by interrupt ID
- no failed or paused branch exposes an uncommitted profile in parent
  `existing`
- pending successful sibling results merge into parent `existing` only after
  every interrupted branch in the superstep is resolved

#### Test 11: `tests/test_defensive_duplicate_branch_boundaries_v3.py`

Expected action: review its future microplan after create recovery is stable.

Keep duplicate-bucket policy separate from recovery policy. Add create-repair
boundary cases only if duplicate/conflicting branches introduce behavior not
already covered by Tests 5 and 10.

### Step 9: Update Supporting Test Plans

After production behavior is stable:

- rewrite `microplans/TEST_CREATE_FAILURE_POLICY_V3_MICROPLAN.md`
- update Test 10 coverage and progress in
  `microplans/PART3_TEST_MACROPLAN.md`
- update stale create-failure statements in
  `microplans/PART3_FANOUT_WRAPPER_INTEGRATION_EDGE_CASES.md`

Do not erase historical completed-test records. Clearly distinguish tests that
were reviewed unchanged from tests that were adapted.

### Step 10: Run Regression Gates

Run affected focused files first:

1. `tests/test_extract_branch_v3.py`
2. `tests/test_create_failure_policy_v3.py`
3. `tests/test_parent_subject_routing_integration_v3.py`
4. `tests/test_parent_multiturn_integration_v3.py`

Then run every currently implemented Part 3 macroplan test and the complete
test suite. Test 11 remains a separate unfinished workflow and should be built
after this create-recovery migration unless its scope is deliberately changed.

## Do Not Break

- one subject per extraction branch
- several supporting messages per subject
- shared messages may support several independent branches
- valid sparse profiles require no repair
- create and update siblings merge through the parent reducer
- completed sibling work survives while another branch is interrupted
- several parallel interrupts can be resumed one at a time by interrupt ID
- update retry, validation, human repair, and commit behavior remain unchanged
- wrapper nodes continue returning valid partial parent-state updates

## Completion Gate

This plan is complete when:

- [ ] the create-recovery contract is implemented
- [ ] UUID generation occurs only in `commit_created_profile(...)`
- [ ] expected create failures retry once and then interrupt for human repair
- [ ] invalid human repair input can be corrected without losing branch state
- [ ] every currently implemented Part 3 MacroPlan test has been reviewed and
      run
- [ ] Tests 5, 7, 8, and 10 are adapted where required
- [ ] Test 11's future microplan has been checked for create-recovery impact
- [ ] focused tests and the full suite pass
- [ ] the MacroPlan and edge-case documentation describe the implemented policy
