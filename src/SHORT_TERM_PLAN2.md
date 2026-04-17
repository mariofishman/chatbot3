1. Freeze the current notebook.

Save the current working version before refactoring anything.

2. Define the new graph on paper.

Write only the node names and edges for the new architecture.

3. Define the planner output schema.

Create the small structured schema that decides:

- which existing ids to update
- how many new objects may need to be created

4. Define the planner node.

Make one node whose only job is to read messages and return that decision schema.

5. Define state boundaries and reducer needs.

Decide which fields belong in:

- main graph state
- extract subagent state
- update subagent state

At the top level, keep only the fields needed by the main planner/router flow.

Document how `messages` should only receive compact summary messages at commit time, and how `existing` should merge committed updates from subagents.

6. Refactor the code to use three state models.

Create:

- one main graph state
- one extract subagent state
- one update subagent state

Remove subagent-local working fields from the top-level state.

7. Refactor extract into a creation subagent.

Do this in three parts:

- define the exact input and output interface of `extract`
- refactor the code in `graphv2.py` so `extract` follows that interface
- add the custom reducer or merge logic needed so `extract` can return only newly created profiles keyed by new ids and have them merged safely into top-level `state.existing`

For the simple version, `extract` should:

- receive `messages`, `existing`, and `plan`
- extract one or more new `UserProfile` objects
- compare the number of extracted profiles against `plan.new_person_count`
- retry once if the counts do not match
- if the counts still do not match after the retry, return an explicit planner/extract mismatch result and route to a human clarification step
- return only the new committed profiles keyed by fresh ids, not the full `existing` dict

7a. Define the create-path mismatch handling.

Decide how the graph should handle the explicit planner/extract mismatch result returned by `extract`.

For the simple version:

- do not merge anything into top-level `state.existing`
- surface the mismatch clearly for inspection
- ask the human for clarification when planner and extractor still disagree after one retry
- route the clarification response back into the create path so `extract` can try again with the additional information
- do not guess which count was correct without clarification

8. Refactor `extract_updates` into an update subagent.

Its only job: produce `PatchProposalList` for the target ids it receives, inside update-local state.

9. Narrow the inputs of `extract_updates`.

Make sure it only receives the ids selected by the planner, not all existing objects.

10. Add a planner and extract consistency check inside `extract`.

Compare `new_person_count` with the number of extracted profiles. If they do not match, retry the extraction once with an extra prompt note describing the mismatch.

11. Keep `apply_patch` as a separate deterministic node inside the update subagent.

Its only job: apply proposed patches to the correct existing objects and write results into update-local candidate state.

12. Keep `validate` as a separate deterministic node inside the update subagent.

Its only job: validate updated candidates and write errors into update-local state.

13. Keep `validate_route` after `validate`.

Its only job: decide between retry/patch or commit.

14. Refactor `patch`.

Its only job: repair invalid candidates using the validation errors inside update-local state.

15. Add a final `commit` node.

Its only job: merge committed results from extract and update subagents into top-level `state.existing`, and add only compact summary messages to top-level `state.messages`.

16. Add the parallel branch wiring.

Allow the planner to trigger both:

- create branch
- update branch

from the same human message.

17. Test only the create path.

Use a message that describes a completely new person.

18. Test only the update path.

Use a message that clearly updates one existing person.

19. Test the mixed path.

Use one message that both updates one person and introduces another.

20. Test planner and extract count mismatch.

Use a case where planner and extract disagree on the number of new profiles and verify the repair path.

21. Verify reducers and merge behavior.

Confirm that parallel writes merge correctly into top-level `state.existing` and that subagent-local working state does not leak into the main graph state.

22. Clean prompt responsibilities.

Planner prompt decides actions only.
Create prompt creates only.
Update prompt patches only.

23. Remove dead logic from the old architecture.

Delete anything no longer used after the refactor.

24. Only then improve memory semantics.

Decide later whether `existing` remains the only canonical committed store or whether you introduce a separate long-term memory layer.
