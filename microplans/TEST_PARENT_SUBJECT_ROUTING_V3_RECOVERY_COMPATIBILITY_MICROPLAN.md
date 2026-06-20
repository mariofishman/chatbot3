# Test Parent Subject Routing V3 Recovery Compatibility Microplan

## Scope

Review and lightly adapt `tests/test_parent_subject_routing_integration_v3.py`
after create-recovery was added inside `extract_subgraph`.

This file should remain a parent happy-path integration test. It should not
become the detailed create-repair test.

## Contract To Preserve

Parent routing still depends on `SubjectBucketList`:

- no-subject batches finish without branch work
- new-classified buckets fan out to create branches
- existing-classified buckets fan out to update branches
- mixed create/update batches merge branch results through the parent reducer
- each branch receives only its supporting messages

Create recovery is internal to the extract branch. Successful first-pass
extraction should still look like a normal committed create from the parent.

## Review Focus

Check whether the deterministic fake LLM still works after `extract_node(...)`
can make additional `UserProfile` calls only on failure.

For this file's existing happy paths, the fake should still return one valid
profile per create branch and should not trigger retry or human repair.

## Tests To Preserve

- no-subject batch
- create-only batch with isolated evidence
- update-only batch with isolated evidence
- mixed create/update batch with branch isolation and merge-back

## Optional Compatibility Assertion

If cheap, add an assertion that parent results do not expose extract-local
`candidate` or `errors` fields.

Do not add detailed recovery cases here; those belong to Test 10.

## Run Command

```bash
.venv/bin/pytest -q tests/test_parent_subject_routing_integration_v3.py
```
