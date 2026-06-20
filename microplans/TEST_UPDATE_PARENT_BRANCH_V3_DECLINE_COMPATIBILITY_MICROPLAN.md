# Test Update Parent Branch V3 Decline Compatibility Microplan

## Scope

Review `tests/test_update_parent_branch_v3.py` after update human repair gained
one-shot submit/decline behavior.

This file focuses on the parent wrapper and routed update payload. It should
not duplicate the detailed update-human-repair matrix from
`tests/test_human_repair_v3.py`.

## Contract To Preserve

- `fan_out_updates(...)` sends exactly one existing profile and only that
  subject's supporting messages
- `run_update_subgagent(...)` forwards only `messages` and `existing` into
  `update_subgraph`
- wrapper output remains a partial parent-state `{"existing": ...}` update
- no-op update branches still return the unchanged profile

## Compatibility Check

If adding one focused case is cheap, simulate a declined update branch by
monkeypatching `graphv3.update_subgraph` to return the unchanged existing
slice. Assert `run_update_subgagent(...)` returns that unchanged slice.

Do not test actual LangGraph interrupts here.

## Run Command

```bash
.venv/bin/pytest -q tests/test_update_parent_branch_v3.py
```
