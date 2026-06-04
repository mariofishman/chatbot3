# Update Patches Micro Plan

This file is a temporary implementation note for `update_patches()` in
`graphv3.py`.

It is intentionally narrower and more disposable than
`SHORT_TERM_PLAN2.md`.

## Goal

Implement the first real node of `update_subgraph`.

`update_patches()` should make one LLM call for one target profile and return
patch proposals, not updated profiles.

## Micro Plan

1. Read the one-user substate.

At this point, the node should assume it receives:

- one target profile inside `state.existing`
- all update-relevant messages for that one target profile inside
  `state.messages`
- `state.reasoning_summary_for_update` as supporting planner background

2. Prepare clean text inputs.

Format three pieces of information for the prompt:

- the target profile as it currently exists
- the relevant messages for that target user
- the shared update reasoning summary

3. Treat the reasoning summary as low-priority background.

Do not add a separate LLM step just to clean the reasoning summary.

Instead, the prompt should explicitly say:

- the summary may mention other users
- the model must ignore summary content that is not relevant to the current
  target profile
- the primary sources of truth are:
  - the one-user existing profile
  - the filtered messages for that user

4. Ask the model only for `PatchProposalList`.

The node should not:

- apply patches
- validate the updated profile
- commit results

Its only job is to propose JSON patch operations for the current target
profile.

## Working Principle

Keep `update_patches()` to one LLM call, not two.

The reasoning summary should be included only as soft context, while the
existing profile plus filtered messages remain the main evidence.
