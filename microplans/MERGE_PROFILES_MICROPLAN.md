# Merge Profiles Microplan

Scope: confirm and, if needed, lightly adjust `merge_profiles(existing, new)`
in `src/state.py` only.

## Relevant inputs

- `src/state.py`, function `merge_profiles(...)`
- `src/state.py`, model `UserProfile`
- `src/graphv3.py`, update flow:
  - `fan_out_updates(...)`
  - `run_update_subgagent(...)`
  - `update_patches(...)`
  - `apply_patch(...)`
  - `commit(...)` docstring

## Architecture conclusion

The reducer is **not** responsible for updating fields inside a `UserProfile`.

That work belongs to the update subgraph:

- parent fan-out sends one target `UserProfile` into each update branch
- `update_patches(...)` proposes field-level changes
- `apply_patch(...)` applies those changes to the current target profile
- `commit()` is intended to return the latest full updated `UserProfile` for
  that user id

So the parent reducer only needs to merge whole `UserProfile` objects by
`user_id` into `MainState.existing`.

## What the function must do

1. Safely handle `None` or empty dict inputs.
2. Merge by `user_id` at the dict level.
3. If the same `user_id` exists in both dicts, keep the `UserProfile` from
   `new`.
4. Keep existing profiles whose ids are not present in `new`.
5. Add brand-new ids from `new`.
6. Return a fresh dict without mutating the inputs.

## What it must not do

- merge scalar fields inside `UserProfile`
- merge list fields such as `interests`
- inspect profile contents semantically
- mutate the input dicts

## Concrete execution target

Treat `merge_profiles(...)` as a simple dict-level overlay reducer for whole
profiles.

This workflow should only:

- confirm that this is the correct semantic role for the function
- make small safety or clarity improvements if needed
- avoid introducing field-level merge behavior

## Assumptions

- `update_subgraph` returns full updated profiles for the user ids it touches.
- Parent state uses `merge_profiles(...)` only to combine those final profile
  objects into `state.existing`.
- Reducer tests should protect this dict-level whole-profile merge behavior.
