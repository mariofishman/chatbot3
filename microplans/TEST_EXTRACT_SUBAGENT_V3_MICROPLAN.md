# Microplan For `tests/test_extract_subagent_v3.py`

## Scope

Create one deterministic pytest-style test file for the create-side extract flow only.

This file should cover:

- `run_extract_subgagent()`
- `extract_node()`

It should not cover the separate `human()` node, which already has its own planned file.

## Input context to test

The test targets these units in `src/graphv3.py`:

- `run_extract_subgagent(state: MainState)`
- `extract_node(state: ExtractAgentState)`

Relevant inputs:Use the MD file review skill on this microplan you just wrote.

- `state.messages`
- `state.plan.relevant_for_create_links`
- `state.plan.reasoning_summary_for_create`
- `state.existing` only insofar as the wrapper should pass `{}` into the extract subgraph

## Output behavior to verify

The test file should verify that `run_extract_subgagent()`:

- filters only create-relevant messages
- passes a narrowed create-side plan into `extract_subgraph`
- passes empty `existing` into the extract-subgraph input
- returns only the `existing` slice produced by the subgraph

The test file should verify that `extract_node()`:

- returns `Command(..., goto="__end__")` when extraction count matches
- retries once when the first extraction count mismatches
- returns `Command(..., goto="human")` when the retry still mismatches
- writes generated IDs into `existing` on success

## Must do

- use deterministic fakes or monkeypatches for:
  - `extract_subgraph.invoke(...)` in the wrapper test
  - `llm.with_structured_output(...).invoke(...)` in the node test
- keep the file focused on the create-side extract flow only
- assert returned payload shape directly

## Must not do

- do not test `human()`
- do not test planner behavior
- do not test update-side routing or update wrappers
- do not depend on live model output

## Assumptions

- one fake wrapper test plus a small set of `extract_node()` path tests is enough for the first version
- `Command` return shape can be asserted directly
- we do not need to test the exact prompt wording, only the control-flow and payload effects
