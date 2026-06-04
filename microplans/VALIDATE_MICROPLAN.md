# Validate Microplan

Scope: implement `validate(state)` in `src/graphv3.py` only.

## Relevant inputs

- `src/graphv3.py`, function `validate(...)`
- `src/graphv3.py`, nearby nodes:
  - `apply_patch(...)`
  - `route_patches(...)`
  - `patch(...)`
  - `commit(...)`
- `src/state.py`, `UpdateAgentState` fields:
  - `candidate`
  - `errors`

## Architecture conclusion

`validate(...)` is the deterministic gate between `apply_patch(...)` and
`route_patches(...)`.

Its job is to inspect the patched raw candidate profile(s) returned by
`apply_patch(...)`, attempt `UserProfile(**candidate_data)` reconstruction,
and turn reconstruction/update-flow failures into `state.errors` instead of
letting them escape as hard exceptions.

It should not:

- call the model
- repair anything
- commit anything
- decide routing itself

## What the function must do

1. Inspect `state.candidate`.
2. Enforce the one-profile update-branch contract:
   - candidate contains exactly one profile
   - candidate key is a non-empty user id string
   - candidate value is a dict-like raw profile payload
3. Attempt `UserProfile(**candidate_data)` reconstruction for that one raw
   candidate.
4. Convert any reconstruction/type/schema failure into
   `{"errors": {target_id: [...]}}`.
5. Return `{"errors": ...}` where:
   - empty means ready for commit
   - non-empty means the branch should go to patch

## What it must not do

- mutate `state.candidate`
- generate new patches
- route to `"patch"` or `"commit"`
- merge anything into parent state

## Concrete execution target

A good first implementation of `validate(...)` should stay small and
deterministic.

It should validate only the structural/update-loop contract for now:

- exactly one candidate profile is present
- that candidate can be reconstructed as `UserProfile`
- failures are recorded in `state.errors`

It should not yet introduce broader business-rule validation such as:

- profile-completeness rules like `name`
- semantic quality checks for fields such as `interests`

## Assumptions

- `apply_patch(...)` now returns patched raw candidate data rather than an
  eagerly validated `UserProfile`.
- This matches the TrustCall-style separation better:
  - patch application first
  - validation/retry loop second
- So `validate(...)` is now the right place to:
  - catch schema/type reconstruction errors
  - enforce the one-profile branch contract
  - populate `state.errors` for `route_patches(...)`
  - keep broader business-rule validation out of scope for the first pass
