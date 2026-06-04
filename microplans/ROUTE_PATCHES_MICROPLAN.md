# Route Patches Microplan

Scope: implement `route_patches(state)` in `src/graphv3.py` only.

## Relevant inputs

- `src/graphv3.py`, function `route_patches(...)`
- `src/graphv3.py`, nearby nodes:
  - `apply_patch(...)`
  - `validate(...)`
  - `patch(...)`
  - `commit(...)`
- `src/state.py`, `UpdateAgentState` fields:
  - `candidate`
  - `errors`

## Architecture conclusion

`route_patches(...)` is a pure routing function inside the update subgraph.

Its job is only to choose:

- `"patch"` when validation has found errors that still need repair
- `"commit"` when the candidate is valid enough to return
- `"human_repair"` when validation errors remain after the retry limit

It must also stop the retry loop once the maximum patch-attempt limit has
been reached.

It should not modify state.

## What the function must do

1. Inspect `state.errors`.
2. If there are no validation errors, return `"commit"`.
3. If there are validation errors and the retry limit has not been reached,
   return `"patch"`.
4. If there are validation errors and the retry limit has already been
   reached, return `"human_repair"` instead of looping again.

## What it must not do

- mutate `state`
- inspect or rewrite `state.patches`
- call the model
- perform validation itself

## Assumptions

- `validate(...)` will write errors into `state.errors`.
- Empty `state.errors` means the branch is ready to commit.
- Non-empty `state.errors` means the branch must go to `patch`, unless the
  retry limit has been exhausted.
- For the first implementation, use a small fixed retry limit of `3`
  patch-attempts.
- The actual `interrupt(...)` should happen in a separate human-repair node,
  not inside `route_patches(...)`.
