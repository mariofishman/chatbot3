# Apply Patch Micro Plan

This file is a temporary implementation note for `apply_patch()` in
`graphv3.py`.

It is intentionally narrower and more disposable than
`SHORT_TERM_PLAN2.md`.

## Goal

Implement the deterministic patch-application step of `update_subgraph`.

`apply_patch()` should not call the LLM. It should take the patch proposals
already produced by `update_patches()` and apply them to the one target
profile in local update state.

## Micro Plan

1. Read the one-user update substate.

At this point, the node should assume it receives:

- one target profile inside `state.existing`
- one or more patch proposals inside `state.patches`

It should enforce the one-user contract explicitly.

2. Match patch proposals to the existing target profile.

Since this subgraph run is one-user-at-a-time, `apply_patch()` should:

- identify the single target `user_id` from `state.existing`
- fail clearly if any patch proposal targets a different id

3. Convert the target profile into a plain mutable structure.

The existing `UserProfile` should be turned into a plain dict so patch
operations can be applied deterministically.

4. Apply patch operations in code, not with the LLM.

For the current simple version, support only the patch operations already
declared in `PatchOp`:

- `add`
- `remove`
- `replace`

Apply them to the target profile in order.

5. Rebuild the updated candidate profile.

After patching the plain dict:

- validate or reconstruct it as `UserProfile`
- write it into `state.candidate` under the same target id

6. Keep this node narrow.

`apply_patch()` should not:

- generate new patches
- validate semantic correctness beyond reconstructing the profile shape
- decide routing
- commit final results

Its only job is deterministic application of the proposed patch operations
into `candidate`.

## Working Principle

This node is the deterministic bridge between:

- model output (`PatchProposalList`)
- update-local candidate state

It should be simple, inspectable, and strict about target-id mismatches.
