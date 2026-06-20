# SHORT_TERM_PLAN3v5

## Purpose

This is the executable roadmap for adding deliberate failure recovery to the
new-subject extraction branch before continuing Test 10 of
`microplans/PART3_TEST_MACROPLAN.md`.

The subject-planning, create fanout, update fanout, wrappers, and parent routing
completed in Part 3 remain in place. This plan changes only what happens inside
each create branch after one new `SubjectBucket` and its supporting messages
reach `extract_subgraph`.

## Status

This roadmap is complete.

The create-recovery work in Steps 1-7 and the update-side parity work in Steps
8-10 have been implemented and covered by the completed Part 3 recovery-test
adaptation queue in `microplans/PART3_TEST_MACROPLAN.md`.

Reference commits:

- `a2ff811c9ef3885ad69ebee503dbed48e22e21ef`: recovery refactor for create
  and update branches
- `5915446`: recovery and defensive testing expansion

## Original Problem

The old create branch performed one structured `UserProfile` extraction and
immediately committed it under a generated UUID.

If extraction failed, the exception stopped the branch. The create branch had
no deliberate model retry, human-repair interrupt, or separate commit boundary.
Test 10 could not freeze a useful create-failure policy until that behavior was
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
5. The human responds through an explicit action envelope:
   - `{"action": "submit", "profile": {...}}`
   - `{"action": "decline"}`
6. A valid response routes to commit. An invalid, missing, or declined response
   ends the branch without creating a profile.
7. `commit_created_profile(...)` generates the UUID and returns the committed
   profile through `state.existing`.

There is no automated extraction graph loop, no human-repair loop, and no
`attempts` field. Human repair interrupts once. If the human cannot provide one
valid profile, the create branch ends without creating a profile. Unexpected
programming or infrastructure errors must still propagate rather than being
misrepresented as repairable profile-validation errors.

## Desired State Contract

Refactor `ExtractAgentState` to carry:

- `subject`: the one new `SubjectBucket` assigned to this branch
- `messages`: only that subject's supporting messages
- `candidate: UserProfile | None`: a valid extracted or human-repaired profile
- `errors: list[str]`: the latest expected extraction or validation errors
- `existing`: populated only by `commit_created_profile(...)`

Important invariants:

- a valid sparse `UserProfile` is a successful candidate
- a profile with no meaningful field values is unusable and follows the
  extraction-error or no-create path
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
                                      | invalid or declined response -> END
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
- invalid, missing, or declined human repair input ends the create branch
  without creating a profile
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

Interrupt once with a concise payload containing:

- the subject label
- a formatted, serializable representation of the supporting messages
- the latest extraction errors
- instructions and examples for the explicit response envelope:
  - `{"action": "submit", "profile": {...}}`
  - `{"action": "decline"}`

Inspect the resumed response envelope before validating a profile.

- `action="submit"` with a valid profile becomes `candidate` and clears
  `errors`
- `action="submit"` with an invalid or missing profile returns no candidate and
  preserves useful failure information
- `action="decline"`, an unknown action, or a missing action returns no
  candidate and preserves a concise reason
- the branch must then route to `END` without committing a profile

Do not ask the human for JSON patches and do not generate a UUID here.
Because LangGraph re-executes an interrupted node from its beginning, keep all
work before `interrupt(...)` free of non-idempotent side effects. Do not call a
second interrupt from this node.

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

Add routing after `human_create_repair(...)`:

- a valid human candidate routes to `commit_created_profile`
- any response that leaves no candidate routes directly to `END`, whether or
  not an explanatory error was recorded

Use a separate post-human routing function. Do not reuse `route_extraction(...)`
because extraction errors with no candidate route to human repair, while the
same state shape after an unsuccessful human response must route to `END`.

Review `run_extract_subgagent(...)`, `fan_out_creates(...)`, and
`route_after_subject_planner(...)` without changing their established parent
contracts:

- one new bucket creates one extraction branch
- the wrapper passes one subject and its supporting messages
- the wrapper returns only the committed partial parent `existing` update
- create and update branches may still run in parallel

### Step 8: Define Update-Side Human Response Parity

Adopt the same one-interrupt UX for `update_subgraph.human_repair(...)`.

The human response envelope is:

- submit corrective patches:
  `{"action": "submit", "patches": {"items": [...]}}`
- decline the update: `{"action": "decline"}`

The update-side policy must be:

- interrupt exactly once after automated patch repair attempts are exhausted
- valid submitted patches continue through `apply_patch(...)`, validation, and
  commit
- declined, malformed, missing-action, or invalid submitted patches end the
  update branch without changing the existing profile
- no second human interrupt occurs
- the branch preserves a concise reason for an unsuccessful human response

Keep the automated update retry loop unchanged. This step changes only the
human-repair UX after the automated retry limit.

### Step 9: Refactor Update Human Repair And Routing

Refactor `human_repair(...)`:

- replace the raw `PatchProposalList` response with the explicit action
  envelope
- inspect `action` before validating submitted patches
- for `action="submit"`, validate `payload["patches"]` as `PatchProposalList`
- require at least one proposal and require every proposal to target the
  current user ID
- return valid patches with cleared errors
- return no patches and preserve a concise reason for decline, malformed
  envelopes, missing/unknown actions, or invalid submitted patches
- remove the current repeated-interrupt validation loop

Add a separate post-human update router:

- valid submitted patches route to `apply_patch(...)`
- every no-patches human outcome routes directly to `END`
- contradictory state fails clearly

Rewire `update_subgraph` so `human_repair(...)` uses this post-human router
instead of its unconditional edge to `apply_patch(...)`.

When a human update is declined or unusable, the branch must end without
returning a changed `existing` slice. The parent therefore keeps the original
profile unchanged.

### Step 10: Review Create And Update Recovery Code

Review both recovery paths together:

- create and update human repair each interrupt once
- both use explicit submit/decline envelopes
- invalid, missing, malformed, unknown-action, and declined responses end
  without committing changes
- valid create submissions commit one profile
- valid update submissions continue through deterministic application,
  validation, and commit
- all work before each interrupt is idempotent
- create UUID generation remains commit-only
- update automated retry, validation, and commit behavior before human repair
  remains unchanged

### Step 11: Review Every Part 3 Macroplan Test

Completed.

All eleven workflows were reviewed before closing the Part 3 recovery-test
adaptation queue. Relevant existing assertions were preserved and only tests
whose contracts were affected were changed.

Before editing previously completed test files, narrow extension microplans
were written and reviewed. New focused and full-suite results were recorded in
`microplans/PART3_TEST_MACROPLAN.md` without erasing earlier completion
history.

#### Test 1: `tests/test_upstream_subject_node_v3.py`

Completed action: run unchanged.

Reason: subject detection and classification happen before extraction recovery.

#### Test 2: `tests/test_state_reducers_v3.py`

Completed action: reviewed and run unchanged.

Reason: the reducer still receives only fully committed profile dictionaries.
Confirm that candidates never reach this reducer before commit.

#### Test 3: `tests/test_update_subgraph_integration_v3.py`

Completed action: reviewed and extended.

Preserve successful and no-op update behavior. Confirm a declined or invalid
human response ends without returning a changed committed profile.

#### Test 4: `tests/test_subject_fanout_v3.py`

Completed action: reviewed and run unchanged.

Reason: `fan_out_creates(...)` must continue sending one subject and its
supporting messages; recovery is internal to the extract subgraph.

#### Test 5: `tests/test_extract_branch_v3.py`

Completed action: substantially extended and adapted.

Preserve current happy-path coverage, then cover:

- valid first extraction commits once
- valid sparse first extraction commits without retry
- first expected failure followed by successful model retry
- two expected failures route to human repair
- valid human repair commits once
- invalid or declined human repair ends without creating a profile
- UUID is absent before commit and generated only after a valid candidate
- wrapper still returns only committed partial parent `existing`

Direct `extract_node(...)` tests must stop expecting immediate `existing`
output and instead assert the candidate/error contract.

#### Test 6: `tests/test_update_parent_branch_v3.py`

Completed action: reviewed and adapted because update decline behavior affects the
wrapper result.

Confirm a declined update branch leaves the parent profile unchanged.

#### Test 7: `tests/test_parent_subject_routing_integration_v3.py`

Completed action: reviewed and adapted its deterministic fake only as needed for the
additional extraction calls.

Preserve all no-subject, create-only, update-only, and mixed happy paths.
Confirm that successful create branches still merge with successful update
branches. Do not duplicate detailed create-repair coverage assigned to Test 10.

#### Test 8: `tests/test_parent_multiturn_integration_v3.py`

Completed action: reviewed and adapted its deterministic fake only as needed.

Preserve all existing multi-turn behavior. Confirm that committed create IDs
remain stable for later updates and that temporary create candidates/errors do
not leak into parent checkpointed state.

#### Test 9: `tests/test_parallel_update_repair_integration_v3.py`

Completed action: substantially extended and adapted.

Preserve existing successful and valid-human-repair behavior, adapted to the
new action envelope. Add coverage for:

- one interrupted update declines while successful siblings are preserved
- several interrupted updates receive mixed submit and decline responses one
  at a time by interrupt ID
- declined branches leave their original profiles unchanged
- no invalid or declined update response interrupts again

#### Test 10: `tests/test_create_failure_policy_v3.py`

Completed action: replaced the stale fail-fast microplan, then created the test
file around the new policy.

Required integration coverage:

- first extraction succeeds without retry or interrupt
- first extraction fails and second model attempt succeeds
- both model attempts fail and produce one human interrupt
- valid human response resumes and commits
- invalid or declined human response ends that create branch without another
  interrupt or committed profile
- one create branch needs human repair while successful create/update siblings
  remain preserved as pending sibling work
- several create branches interrupt and resume one at a time by interrupt ID
- no failed or paused branch exposes an uncommitted profile in parent
  `existing`
- pending successful sibling results merge into parent `existing` only after
  every interrupted branch in the superstep is resolved

#### Test 11: `tests/test_defensive_duplicate_branch_boundaries_v3.py`

Completed action: reviewed and implemented after create recovery was stable.

Duplicate-bucket policy remained separate from recovery policy. The completed
test freezes only the safe current policy: duplicate existing buckets with the
same `candidate_existing_id` are merged inside `subject_planner_node(...)`
before fanout. Duplicate new-label ambiguity remains deferred to future
persistence-backed identity resolution.

Also review these focused update-side files even though they are not separate
numbered MacroPlan workflows:

- `tests/test_human_repair_v3.py`: substantially rewritten around the one-time
  action envelope and post-human routing
- `tests/test_route_patches_v3.py`: confirmed routing into human repair remains
  unchanged
- `tests/test_patch_v3.py`, `tests/test_validate_v3.py`, and
  `tests/test_commit_v3.py`: run unchanged to guard the automated update loop

### Step 12: Update Supporting Test Plans

Completed after production behavior stabilized:

- rewrote `microplans/TEST_CREATE_FAILURE_POLICY_V3_MICROPLAN.md`
- updated Test 10 and Test 11 coverage and progress in
  `microplans/PART3_TEST_MACROPLAN.md`
- updated stale create-failure and duplicate-boundary statements in
  `microplans/PART3_FANOUT_WRAPPER_INTEGRATION_EDGE_CASES.md`

Historical completed-test records were preserved. Tests reviewed unchanged were
kept distinct from tests that were adapted.

### Step 13: Run Regression Gates

Completed.

Affected focused files were run first:

1. `tests/test_extract_branch_v3.py`
2. `tests/test_human_repair_v3.py`
3. `tests/test_update_subgraph_integration_v3.py`
4. `tests/test_parallel_update_repair_integration_v3.py`
5. `tests/test_create_failure_policy_v3.py`
6. `tests/test_parent_subject_routing_integration_v3.py`
7. `tests/test_parent_multiturn_integration_v3.py`

Then every currently implemented Part 3 macroplan test and the complete test
suite were run through the macroplan workflow. Test 11 was built after the
create-recovery migration and now closes the defensive duplicate-boundary
queue.

## Do Not Break

- one subject per extraction branch
- several supporting messages per subject
- shared messages may support several independent branches
- valid sparse profiles require no repair
- create and update siblings merge through the parent reducer
- completed sibling work survives while another branch is interrupted
- several parallel interrupts can be resumed one at a time by interrupt ID
- update automated retry, validation, and commit behavior remain unchanged
- wrapper nodes continue returning valid partial parent-state updates

## Completion Gate

This plan is complete when:

- [x] the create-recovery contract is implemented
- [x] UUID generation occurs only in `commit_created_profile(...)`
- [x] expected create failures retry once and then interrupt for human repair
- [x] invalid or declined human repair input ends the branch without creating a
      profile or interrupting again
- [x] update human repair interrupts once and uses the submit/decline envelope
- [x] invalid or declined update human repair ends without changing the profile
      or interrupting again
- [x] every currently implemented Part 3 MacroPlan test has been reviewed and
      run
- [x] Tests 3, 5, 6, 7, 8, 9, and 10 are adapted where required
- [x] Test 11's microplan has been checked, updated, and implemented after
      create recovery stabilized
- [x] focused tests and the full suite pass
- [x] the MacroPlan and edge-case documentation describe the implemented policy
