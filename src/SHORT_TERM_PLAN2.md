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

5. Decide which state fields need reducers.

List only the fields that parallel branches may write to.

6. Refactor extract into a creation subagent.

Its only job: extract one or more new UserProfile objects and write them into `state.candidate`.

7. Refactor `extract_updates` into an update subagent.

Its only job: produce `PatchProposalList` for the target ids it receives.

8. Narrow the inputs of `extract_updates`.

Make sure it only receives the ids selected by the planner, not all existing objects.

9. Add a planner and extract consistency check inside `extract`.

Compare `new_person_count` with the number of extracted profiles. If they do not match, retry the extraction once with an extra prompt note describing the mismatch.

10. Keep `apply_patch` as a separate deterministic node.

Its only job: apply proposed patches to the correct existing objects and write results into `state.candidate`.

11. Keep `validate` as a separate deterministic node.

Its only job: validate updated candidates and write errors to state.

12. Keep `validate_route` after `validate`.

Its only job: decide between retry/patch or end.

13. Refactor `patch`.

Its only job: repair invalid candidates using the validation errors.

14. Add the parallel branch wiring.

Allow the planner to trigger both:

- create branch
- update branch

from the same human message.

15. Test only the create path.

Use a message that describes a completely new person.

16. Test only the update path.

Use a message that clearly updates one existing person.

17. Test the mixed path.

Use one message that both updates one person and introduces another.

18. Test planner and extract count mismatch.

Use a case where planner and extract disagree on the number of new profiles and verify the repair path.

19. Verify reducers.

Confirm that parallel writes merge correctly into `state.candidate`.

20. Clean prompt responsibilities.

Planner prompt decides actions only.
Create prompt creates only.
Update prompt patches only.

21. Remove dead logic from the old architecture.

Delete anything no longer used after the refactor.

22. Only then improve memory semantics.

Decide later whether `candidate` remains canonical memory or whether you introduce a separate committed store.
