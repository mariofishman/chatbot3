# SHORT_TERM_PLAN3

This file is not a step-by-step implementation plan yet.

It is a holding place for the next round of improvements we already know we want, after the simpler goals in `SHORT_TERM_PLAN2.md` are finished.

## Improvement Ideas

- Improve `extract_node` so create-side validation is not based only on profile count. Add stronger checks for whether the extracted people are actually the right people, including lightweight validation of names or identity evidence from the planner summary and create-relevant messages.

- Improve `extract_node` repair behavior so it does not always re-run the full extraction set. Explore a more targeted repair path that fixes only the missing, extra, merged, or wrongly split person instead of regenerating every extracted profile from scratch.

- Improve `planner_node` prompt/context strategy so it does not always receive all prior messages and all existing profiles. As memory grows, this could overwhelm the context window, so we need a narrower way to pass only the most relevant conversational evidence and candidate existing profiles into planning.

- Improve the human clarification UX inside the create/extract subagent so the human does not always need to return a full `UserProfileList` payload. Explore a future interaction where the human can provide simpler clarification information and the model can then reprocess the extraction using that clarification instead of requiring a fully corrected structured result from the human.

- Improve the human correction UX so the human can provide only the missing or corrected part of the extraction rather than re-entering everything. A future version should be able to show what the model already got right, ask the human only for the missing or incorrect part, and treat the human response more like a patch than a full replacement.
