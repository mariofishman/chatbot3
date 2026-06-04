# Patch Microplan

Scope: implement `patch(state)` in `src/graphv3.py` only.

## Relevant inputs

- `src/graphv3.py`, function `patch(...)`
- `src/graphv3.py`, nearby nodes:
  - `update_patches(...)`
  - `apply_patch(...)`
  - `validate(...)`
  - `route_patches(...)`
- `src/state.py`, `UpdateAgentState` fields:
  - `messages`
  - `existing`
  - `reasoning_summary_for_update`
  - `candidate`
  - `errors`
  - `attempts`
  - `patches`

## Architecture conclusion

`patch(...)` is the repair-generation step in the update retry loop.

Its job is to read the failed update-local state after `validate(...)`,
especially:

- the current failed raw `candidate`
- the validation errors in `state.errors`

and ask the model for a corrected set of patch proposals for the same one
target profile.

Here, `state.candidate` means the raw patched dict payload for the profile,
not a validated `UserProfile` object.

The next loop should be:

- `patch(...)` generates corrected patch proposals
- `apply_patch(...)` applies them
- `validate(...)` checks them again

## What the function must do

1. Enforce the one-profile update-branch contract from `state.existing`.
2. Require exactly one raw candidate profile in `state.candidate`.
3. Require non-empty `state.errors`, because this node should only run after
   failed validation.
4. Build a repair prompt using:
   - the one target existing profile as baseline context
   - the current failed raw candidate as the thing to repair
   - the same filtered update messages
   - the shared update summary as supporting context
   - the current validation errors
5. Call the structured-output model for `PatchProposalList`.
6. Return the replacement patch proposals in `{"patches": ...}`.
7. Increment `attempts` by one so the retry loop has state.

## What it must not do

- apply the patches itself
- validate the result itself
- commit anything
- mutate parent state
- merge fields directly into `existing`

## Assumptions

- `apply_patch(...)` returns raw patched dict data in `candidate`.
- `validate(...)` converts `UserProfile(**candidate_data)` failures into
  `state.errors`.
- `route_patches(...)` sends control here only when `state.errors` is
  non-empty.
- The corrective prompt should repair the current failed candidate, not
  restart from the original profile alone.
- The first version of `patch(...)` can stay simple:
  - no max-attempt cutoff yet
  - no special branching for different error categories
  - just one corrective structured-output call based on current errors
