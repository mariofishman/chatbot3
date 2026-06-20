# Test Parent Multiturn V3 Recovery Compatibility Microplan

## Scope

Review and lightly adapt `tests/test_parent_multiturn_integration_v3.py` after
create-recovery introduced extract-local candidates and errors.

This file should keep testing checkpointed parent behavior, not detailed
create-repair behavior.

## Contract To Preserve

- messages accumulate within one thread without duplication
- different thread IDs keep message history isolated
- created profiles can be selected and updated in later turns
- no-subject later turns preserve existing profiles and clear buckets

## Recovery Compatibility Focus

After the create branch refactor:

- committed create IDs must remain stable for later update turns
- extract-local `candidate` and `errors` must not leak into parent
  checkpointed state
- successful first-pass creates should still require only one `UserProfile`
  fake response

## Tests To Preserve

- sparse create, later enrichment, later correction
- several created profiles, then one selected update
- no-subject later turn
- same-thread accumulation and different-thread isolation

## Optional Compatibility Assertion

Inspect `graph.get_state(config).values` after create turns and assert parent
state keys do not include extract-local `candidate` or `errors`.

Do not add create failure or human-create-repair cases here; those belong to
Test 10.

## Run Command

```bash
.venv/bin/pytest -q tests/test_parent_multiturn_integration_v3.py
```
