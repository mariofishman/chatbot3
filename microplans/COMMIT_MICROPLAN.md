# Commit Microplan

Scope: implement `commit(state)` in `src/graphv3.py` only.

## Relevant inputs

- `src/graphv3.py`, function `commit(...)`
- `src/graphv3.py`, nearby nodes:
  - `validate(...)`
  - `route_patches(...)`
  - `patch(...)`
- `src/state.py`, `UpdateAgentState` fields:
  - `candidate`
  - `errors`
  - `existing`

## Architecture conclusion

`commit(...)` is the final step of the update subgraph.

Its job is to take the one validated raw candidate that has already passed
`validate(...)`, reconstruct it as a final `UserProfile`, and return only the
committed `{user_id: UserProfile}` slice that the parent reducer can merge
into `MainState.existing`.

## What the function must do

1. Enforce the one-profile update-branch contract from both:
   - `state.existing`
   - `state.candidate`
2. Require empty `state.errors`, because this node should only run after a
   successful `validate(...)`.
3. Require the candidate user id to match the existing target user id.
4. Reconstruct the raw candidate payload as a final `UserProfile`.
5. Return `{"existing": {target_id: validated_profile}}`.

## What it must not do

- call the model
- generate patches
- repair anything
- return the full parent `existing` dict
- merge parent state directly

## Assumptions

- `validate(...)` is the gate before this node and should already have caught
  reconstruction/type errors.
- So `commit(...)` can stay small and deterministic.
- The parent graph expects only the one committed update slice, not the whole
  merged memory state.
