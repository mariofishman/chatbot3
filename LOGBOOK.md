# Project Logbook 1 - Professional Profile Chatbot. Toy example with ReAct agents.

[Project README](README.md)
[Project Guidelines](GUIDELINES.md)
[Agent Instructions](AGENTS.md)

## Project Introduction

This project aims to build a chatbot that can hold a natural conversation while gradually learning important details about a user's professional background.

The goal is not to force the user through a rigid form. Instead, the system should quietly collect useful facts over time, organize them into a structured profile, and preserve that profile in a reliable way.

This is not only about learning one person's profile during one conversation. The broader goal is to gradually develop a shared and standardized profile structure across many users, while still allowing the system to discover new useful concepts when they emerge.

This is also a learning project. Codex should help the user learn step by step during implementation, rather than impose a fixed plan for how the system must be built.

The current architectural direction is provisional. It exists to help early implementation get started, and it may change as the user learns more, tests ideas, and refines the system.

## 📅 Log Entry: March 25th, 2026 - Initial Project Setup

### Project Direction Clarified

**What was established:**

- The chatbot should learn professional information gradually through natural conversation.
- The system should build a structured profile over time rather than regenerate the entire profile on every turn.
- The project should support both user-specific profile growth and cross-user standardization of important concepts.
- The architecture should remain flexible at this stage and should not be treated as a fixed plan.

**Core architectural ideas currently in scope:**

- A stable top-level graph state with evolving contents.
- A `profile` object for current user facts.
- A `key_registry` for canonical keys and reusable field definitions.
- Partial updates, patches, or deltas instead of full-object regeneration.
- Deterministic validation and merge logic to protect the canonical profile from noisy model outputs.

**Rationale:**

- A fixed state envelope makes the graph easier to reason about and evolve safely.
- Separating current values from canonical structure helps the system stay consistent across many users.
- Patch-style updates are a better fit for a profile that should grow incrementally over time.

### Collaboration Style Established

**What was established:**

- Codex should act as a guide, not the main implementer.
- Code should not be written unless the user explicitly asks for it.
- Guidance should be step-by-step rather than delivered as a large solution.
- Explanations should be short, clear, and focused on learning.

**Concrete outcome:**

- `AGENTS.md` was created and refined to document the expected collaboration style for this repository.

### Repository Foundations Completed

**What was completed:**

- Git was initialized for the project.
- A `.gitignore` was added to avoid committing local environment files and secrets.
- Initial project documentation files were created:
  - `README.md`
  - `GUIDELINES.md`
  - `CONTEXT.md`
  - `AGENTS.md`

**Important clarification reached:**

- The design notes should guide the work without becoming a rigid specification.
- The logbook should evolve over time and record what was decided, clarified, changed, or learned.

### Current Stage

The project is still at an early stage.

The core idea, collaboration rules, and initial architectural direction have been documented, but implementation is only beginning.

### If Starting a New Chat

Use this file together with `AGENTS.md` and `GUIDELINES.md` to restore the main project context quickly.

## 📅 Log Entry: March 25th, 2026 - Initial Graph and Studio Setup

### First Graph Implementation Started

**What was completed:**

- A first version of `src/graph.py` was written.
- The graph uses a simple ReAct-style loop with tool calling.
- A dummy math toolset was introduced as the first test tool surface.
- The first tool scope was intentionally kept small: add, multiply, and divide behavior for basic graph testing.

**Rationale:**

- A minimal tool-using graph is a good first implementation slice.
- It provides working infrastructure for message flow, tool calling, and tracing before profile-learning logic is added.

### LangGraph Studio Connection Established

**What was completed:**

- A root `langgraph.json` file was added so the project can be loaded by LangGraph Studio.
- LangSmith tracing environment variables were configured in `.env`.
- The project was run with `langgraph dev`.
- The local LangGraph API and Studio URL were successfully started.

**Issues found and resolved during setup:**

- A module import path issue prevented the graph from loading in Studio.
- A model initialization issue in `ChatOpenAI` also prevented startup.
- Both issues were fixed so the graph could load in the local LangGraph development server.

**Concrete outcome:**

- The project is now connected to LangGraph Studio and ready for interactive testing and trace inspection.

### Development Workflow Clarified Further

**What was clarified:**

- The user wants debugging guidance in a teaching style, not just direct fixes.
- Error handling support should explain how to read the traceback and identify the failing line before moving to the correction.
- For LangChain and LangGraph questions, `AGENTS.md` was updated so Codex should consult the LangChain MCP documentation tool before answering.

### Remote Repository Created

**What was completed:**

- A GitHub repository for the project was created.
- The local repository was connected to the GitHub remote over SSH.
- The `main` branch was pushed successfully and set to track `origin/main`.

**Concrete outcome:**

- The project now has a remote backup and a clean online checkpoint for future work.

## 📅 Log Entry: March 26th, 2026 - Subagent Architecture Planning

### Subagent Direction Chosen

**What was established:**

- The next stage of the project should move beyond toy tool calling and begin introducing a subagent pattern.
- The first implementation direction chosen was to create a subagent and wrap it behind a tool interface.
- The subagent should remain narrow in scope at first and act as a bounded capability rather than a fully open-ended multi-agent system.

**Rationale:**

- This direction is closer to the real architecture the project will eventually need.
- It preserves the learning-oriented approach by introducing only one new level of complexity at a time.

### Short-Term Implementation Plan Created

**What was completed:**

- A dedicated `SHORT_TERM_PLAN.md` file was created to guide the next implementation stage.
- The plan was intentionally written as a working plan rather than a rigid specification.
- The early steps focus on subagent scaffolding, tool preparation, and a reusable agent-construction utility.

**Important clarification reached:**

- The tool-preparation steps were separated from the later subagent-construction step.
- This made the plan more accurate: tools can be prepared first, and only attached to a concrete subagent later.

### Subagent Model Scaffolded

**What was completed:**

- A `Subagent` model was introduced in `src/graph.py`.
- The model captures the basic configuration needed for a specialized agent:
  - `name`
  - `description`
  - prompt/system-prompt field
  - `tools`
- Optional tool configuration was handled with a default empty list.

**Rationale:**

- This establishes a clear separation between subagent configuration and subagent runtime construction.
- It also creates a stable place for expanding agent metadata later.

### Initial Tool Set Expanded

**What was completed:**

- The initial math tool set was kept and clarified as the first tool surface for subagent experimentation.
- A new `subtract()` tool was added.
- The tool set now covers the full basic arithmetic group needed for simple delegated testing:
  - add
  - subtract
  - multiply
  - divide

**Concrete outcome:**

- The project now has a more complete toy tool surface for testing subagent invocation patterns.

### Agent Builder Refactor Started

**What was clarified and implemented:**

- A reusable builder utility was introduced in `src/builder.py`.
- The graph-construction logic began moving out of `src/graph.py` into this reusable builder.
- It was clarified that the model should be treated as a builder-time dependency rather than passed through graph state.
- It was also clarified that the node function should be constructed inside the builder once the model and tools are known.

**Rationale:**

- This keeps graph construction cleaner.
- It supports the upcoming step of creating multiple compiled agents from different `Subagent` configurations.

### Development Approach Reinforced

**What was reinforced:**

- The project should continue moving step by step.
- The implementation plan should be updated as understanding improves.
- Architectural decisions made at this stage should remain provisional and easy to revise.

## 📅 Log Entry: March 28th, 2026 - Steps 5 and 6: Compiled Subagents and Delegation Context

### Step 5 Completed

**What was completed:**

- The first concrete subagents were created from the `Subagent` model.
- Two subagents were introduced instead of one:
  - a math subagent
  - a search subagent
- The reusable agent-construction utility was updated so it can optionally accept a system prompt.
- A compiled subagent dictionary of the form `{name: compiled_agent}` was created.

**Important clarification reached:**

- Passing actual tool objects into the `Subagent` model was accepted as the right direction.
- The `tools` field was updated to use tool objects rather than string names.
- It was also clarified that an optional prompt should default to `None` and only be turned into a `SystemMessage` when present.

**Concrete outcome:**

- Step 5 of `SHORT_TERM_PLAN.md` is now complete.
- The project now has multiple compiled subagents available for later delegation through the main agent.

### Current Position

The project now has:

- a reusable agent builder,
- a `Subagent` configuration model,
- a compiled subagent map,
- a working local LangGraph testing flow through both Studio and direct API calls.

This leaves the next meaningful implementation steps focused on:

- creating the string that lists available agents,
- building the main-agent tool that delegates to them,
- and then wiring the main agent around that delegation pattern.

### Step 6 Completed

**What was completed:**

- A single formatted string was created to list the available subagents and what each one is for.
- The string is derived from the current subagent definitions rather than written manually.
- A task-description prefix and formatted task description were added to support upcoming delegation work.

**Rationale:**

- This creates a clean bridge between subagent configuration and the future main-agent delegation tool.
- It keeps the available-agent context centralized and easier to maintain as more subagents are added.

## 📅 Log Entry: March 28th, 2026 - Where I Stopped

### Progress Since the Previous Entry

**What was completed:**

- Work began on step 7 by introducing a main-agent tool called `select_subagent` in `src/graph.py`.
- The main agent was reconfigured to use `select_subagent` as its tool surface instead of the raw math tools.
- The `select_subagent` tool was designed to:
  - receive a task description,
  - receive an `agent_name`,
  - access graph state through `ToolRuntime`,
  - append a `HumanMessage` for the delegated task,
  - invoke the selected compiled subagent,
  - return the final content from the subagent's last message.

**Current code shape at the stopping point:**

- `src/graph.py` contains:
  - the `Subagent` model,
  - two configured subagents (`math_agent` and `search_agent`),
  - a compiled `agents` dictionary,
  - a formatted delegation-context string,
  - the new `select_subagent` tool,
  - the main graph compiled with `select_subagent` as its tool.
- `src/my_create_agent.py` still provides the shared ReAct-style graph builder with optional system prompt support.

### Blocking Error Encountered

The exact error encountered at the stopping point was:

```text
BadRequestError('Error code: 400 - {\'error\': {\'message\': "An assistant message with \'tool_calls\' must be followed by tool messages responding to each \'tool_call_id\'. The following tool_call_ids did not have response messages: call_Ncsw5nCEqMlsoxxpsY6KscsH", \'type\': \'invalid_request_error\', \'param\': \'messages.[3].role\', \'code\': None}}')
```

### Interpretation at the Stopping Point

- The project had reached the first real attempt at delegation through the main-agent tool.
- The current blocker appears to be in the tool-call/message lifecycle around subagent invocation, not in the earlier subagent configuration steps.
- This is the point to resume from when work starts again.

## 📅 Log Entry: March 29th, 2026 - Steps 7 and 8 Completed: Delegation Working End to End

### The Step 7 Error Was Diagnosed and Fixed

**What happened:**

- The main agent correctly selected `select_subagent` and reached the tool node, but execution failed there.
- The failing behavior came from passing the parent agent's message history into the delegated subagent call and then appending a new `HumanMessage` to that inherited history.
- This created an invalid message sequence because the parent history already contained an `AIMessage` with unresolved `tool_calls`.

**How it was fixed:**

- The delegated subagent call was changed to use isolated context instead of reusing the full parent message history.
- The delegated state now sends only a fresh task-specific `HumanMessage` to the subagent.
- This preserved the intended isolated-subagent design and removed the invalid tool-call/message ordering.

**Why this fix matters:**

- It clarified that delegated subagents should not automatically inherit the parent conversation history.
- If future subagents need parent context, that context should be passed intentionally rather than by forwarding the entire message list.

### Step 7 Completed

**What was completed:**

- The main-agent tool `select_subagent` now works.
- The main agent can:
  - choose a subagent by name,
  - pass task-specific input,
  - invoke the compiled subagent,
  - return the subagent's result back into the main-agent flow.

**Concrete evidence:**

- The main agent successfully delegated math questions to `math_agent`.
- The main agent successfully delegated research questions to `search_agent`.
- The main agent also responded normally when delegation was not needed.

### Step 8 Completed

**What was completed:**

- The shared `my_create_agent(...)` utility is now used to create the main agent as well as the subagents.
- This completed the short-term architecture goal of using one reusable builder across the whole mini project.

### Current Position

The first short-term implementation cycle is now complete.

The mini project successfully demonstrated:

- a reusable ReAct-style graph builder,
- configurable subagent definitions,
- compiled subagents,
- delegation context for choosing among subagents,
- a main-agent tool that delegates correctly,
- a main agent that can either delegate or answer directly.

### Next Step

The next implementation move should be to create a new `SHORT_TERM_PLAN2.md` for the next phase of the project.

# Project Logbook Part 2 - TrustCall inspiration for memory manager. Bringing a prototype from colab

## 📅 Log Entry: April 5th, 2026 - Notebook Prototype Consolidation and Memory Graph Direction

### Work Continued Outside the Repo Before Returning Here

**What was clarified:**

- The memory-learning architecture was advanced mainly in a Colab notebook before work resumed here in the repository.
- The notebook became the main place where the profile-extraction and profile-update workflow was explored and tested.
- Only recently, after feeling more comfortable with the direction, the work was brought back into this repo through `src/SHORT_TERM_PLAN2.md` and `src/graphv2.py`.

**Concrete outcome:**

- The repository now reflects a later-stage architecture discussion than the earlier toy subagent work in `src/graph.py`.

### Notebook Prototype Was Frozen Into the Repo

**What was completed:**

- The notebook `learning_memoryv2.ipynb` was converted into `src/graphv2.py`.
- This file was intentionally kept as a frozen baseline of the notebook prototype rather than refactored immediately.
- `src/SHORT_TERM_PLAN2.md` was also reformatted so the numbered steps are easier to read and maintain.

**Rationale:**

- Freezing the notebook work into a Python file creates a stable checkpoint before major architectural changes begin.
- This preserves the prototype while making the next steps easier to discuss inside the codebase.

### Trustcall Was Confirmed as the Main Architectural Inspiration

**What was established:**

- `src/SHORT_TERM_PLAN2.md` is explicitly inspired by the Trustcall library, especially `trustcall/_base.py`.
- The main ideas taken from Trustcall are:
  - separation between initial extraction and updates
  - patch-style model proposals instead of full rewrites
  - deterministic patch application
  - validation after updates
  - explicit retry or repair behavior

**Important clarification reached:**

- The goal is not to copy Trustcall literally.
- The goal is to keep the same separation of concerns while building a simpler and more explicit system.

### Architecture Was Reconsidered and Re-decided

**What was discussed:**

- Two possible directions were compared:
  - a ReAct-style main agent using `select_subagent`
  - an explicit planner node followed by deterministic routing

**What was decided:**

- The project should now follow an explicit planner-plus-router architecture.
- A planner node should read the conversation and return a structured planning result.
- Graph routing should then deterministically send execution to:
  - `extract`
  - `update`
  - or both in parallel

**Rationale:**

- This is closer to the Trustcall-style separation between model decision and deterministic execution.
- It creates a clearer decision boundary that is easier to inspect, debug, and log.

### Extract and Update Responsibilities Were Clarified

**What was established:**

- `extract` should be treated as a creation workflow.
- `extract` must support creating one or more `UserProfile` objects from a single message.
- `update` should remain a deterministic mini-graph, not a free-form ReAct workflow.
- The intended update flow remains:
  - `extract_updates`
  - `apply_patch`
  - `validate`
  - `patch` if needed

**Important clarification reached:**

- The reusable `my_create_agent(...)` helper is not the right abstraction for either `extract` or `update`.
- It remains useful for message-in, tool-calling, message-out ReAct behavior, but the memory workflows need different construction.

### PlannerOutput and the Plan Were Refined

**What was completed:**

- A `PlannerOutput` schema was introduced in `src/graphv2.py`.
- The planning structure now reflects:
  - which existing ids should be updated
  - whether new objects should be created
  - how many new objects should be created
  - a short reasoning summary for traceability and prompt debugging

**What was clarified:**

- The reasoning summary should stay short and factual rather than exposing chain-of-thought.
- `src/SHORT_TERM_PLAN2.md` was updated so the planner and extract steps better reflect multi-create behavior.

### The Step-2 Diagram Was Reviewed

**What was established:**

- A diagrams.net workflow drawing was created for the new architecture.
- The drawing correctly captured the high-level separation between create and update paths.

**Issue found:**

- The diagram still reflected a ReAct `select_subagent` main agent and incorrectly showed the update branch using `llm.with_structured_output(UserProfile)`.

**Clarification reached:**

- The drawing should be updated to show:
  - planner node
  - router
  - `extract` as a multi-create path
  - `update` beginning with `llm.with_structured_output(PatchProposalList)` and then continuing through deterministic nodes

### Current Stage

The project has now moved beyond the earlier toy subagent experiments and into a more serious memory-graph design phase.

The notebook prototype has been preserved, Trustcall has been confirmed as the main reference, and the current direction is now an explicit planner-plus-router architecture with deterministic update handling.

### Next Step

The next implementation move is to define the planner node cleanly on top of this newly clarified architecture.

## 📅 Log Entry: April 6th, 2026 - Workflow Diagram Finalized

### Workflow Clarification Completed

**What was completed:**

- The workflow discussed on April 5th was refined and finalized as a diagram.
- The final version now reflects the current architecture clearly:
  - planner node with `PlannerOutput`
  - deterministic router
  - `extract` branch for one or more new profiles
  - `update` branch for patch-based updates and validation
- The workflow was saved as `memory-agent.pdf`.

**Important clarification reached:**

- `extract` is now treated as a multi-profile extraction workflow rather than a single-profile extractor.
- The planner's `new_person_count` is now part of the extract consistency check, with retry logic when counts do not match.

### Current Position

The workflow is now defined clearly enough to move into implementing the planner node in `src/graphv2.py`.

## 📅 Log Entry: April 11th, 2026 - Planner Node Testing and Architecture Pressure

### Planner Node Began Producing Useful Results

**What was completed:**

- `planner_node` in `src/graphv2.py` was brought to a testable state.
- The planner was successfully run in Studio using `agent_v2`.
- A second graph entry was added to `langgraph.json` so both the older graph and `graphv2` can be loaded in Studio.

**Important issue found:**

- `langgraph dev` rejected the graph when `graphv2` was compiled with `InMemorySaver`.
- It was clarified that custom checkpointers should be removed for Studio usage and only enabled for local script-style testing if needed.

### State Semantics Became Clearer

**What was clarified:**

- `existing` should remain the trusted baseline memory.
- `candidate` should remain provisional working state.
- This exposed the need for a final `commit` step to merge validated `candidate` updates back into `existing`.
- `src/SHORT_TERM_PLAN2.md` was updated accordingly so the plan now includes the `commit` node and the merge concern for `existing`.

### Planner Quality Concerns Appeared

**What was observed:**

- The planner handled some mixed-message cases correctly, but it also missed at least one expected subject update.
- This raised the question of whether prompt improvement alone is sufficient or whether additional validation around the planner will eventually be needed.

### Current Position

The planner node now works well enough to expose architectural issues that were not visible before testing.

The project is still implementation-driven in `src/graphv2.py`, but the testing pressure is already revealing where the architecture needs to become more precise.

## 📅 Log Entry: April 12th, 2026 - Robust North-Star Architecture Exploration

### Work Shifted Back From Coding to Architecture

**What happened:**

- Work temporarily stepped back from direct implementation in order to rethink the memory workflow at a more robust architectural level.
- The goal of this discussion was not to replace the current short-term plan, but to define a stronger long-term “north star” architecture that can guide future short-term plans.

### The Workflow Was Expanded Beyond Planner-Only Thinking

**What was clarified:**

- A stronger architecture should separate:
  - memory-worthiness detection
  - subject detection
  - candidate retrieval
  - identity resolution
  - action proposal
  - proposal validation
  - branch-specific extraction/update validation
  - deterministic commit

**Important conceptual improvement:**

- The architecture must explicitly account for profile-worthy facts that are not simple facts about one already-resolved person.
- This led to a new branch for target-scope classification of non-simple facts.

### Non-Simple Fact Cases Were Identified

**What was established:**

- The following conceptual cases were distinguished:
  - fact about one identified subject
  - fact about multiple explicitly identified subjects
  - fact about a subset of subjects selected by a condition
  - fact about all subjects in scope
  - new entity linked to a known subject
  - fact about a non-subject entity
  - unresolved target

**Why this matters:**

- This shifted the discussion from “orphan facts” to a more precise idea of target scope.
- It also exposed where the current `UserProfile`-only memory model will eventually need to evolve into a more relational system.

### Interrupts and Concurrency Were Reconsidered

**What was clarified:**

- If one message contains both resolved and unresolved items, the unresolved part should not conceptually freeze the whole system forever.
- A single monolithic graph run is therefore a poor long-term unit of work for this problem.
- A more robust long-term architecture likely requires item-level task emission and independent worker processing rather than one large synchronized execution.

**Important clarification reached:**

- LangGraph can support pieces of this through workers and `Send`, but a true fire-and-forget task system would still need architecture on top of LangGraph rather than coming “for free.”

### Current Position

The project now has two layers of architecture in mind:

- the current near-term planner-router implementation path in `src/graphv2.py`
- a more robust future architecture centered on task decomposition, identity resolution, non-simple fact scope handling, and stronger concurrency boundaries

This architectural north star is not yet the implementation target, but it now exists as a clearer long-term guide.

## 🧭 Special Entry: April 12th, 2026 - memory_agent.drawio.xml

### Reference File

The file [memory_agent.drawio.xml](/Users/mariofishman/projects/chatbot3/memory_agent.drawio.xml) in the project root should be treated as the current north-star architecture reference for the memory system.

This is not the same as the short-term implementation plan. The short-term work should still follow `src/SHORT_TERM_PLAN2.md` and the current implementation work in `src/graphv2.py`, but this diagram captures the broader architectural direction that future iterations may grow into.

### Why This Entry Exists

This entry is meant to help recover the architectural context later without having to reconstruct the whole discussion from memory.

The key point is that this diagram is intentionally more ambitious than the current implementation. It records the strongest version of the architecture the project could currently articulate, including branches and design concerns that are not yet ready to be built.

### Main Top-Level Flow

The main conceptual flow currently represented in `memory_agent.drawio.xml` is:

- memory-worthiness gate
- subject and fact detection
- candidate retrieval / filtering
- identity resolution
- action proposal
- proposal validator
- proposal repair loop
- deterministic routing into create or update work
- validation and commit into canonical memory

This top-level flow separates decision-making from downstream extraction and patching. That separation remains one of the main architectural values in the project.

Another important reminder is that the north-star diagram is doing two jobs at once:

- describing a conceptual control flow
- preserving open design problems that are not yet settled

So some boxes are intended as stable workflow components, while others are intentionally placeholders for future architectural work.

### Memory-Worthiness Gate

The first node asks whether a message contains profile-worthy information at all.

This is intended as a lightweight gate, not a deep semantic planner. The purpose is simply to avoid doing expensive downstream work on messages that should not affect memory.

### Subject and Fact Detection

The second node identifies the people mentioned in the message and also detects profile-worthy facts that are not simple subject-scoped statements.

This area of the architecture became more important over time because it became clear that not all useful memory facts are cleanly reducible to “one known person, one known field.”

One subtle but important clarification is that this node should not be treated as the place where all target resolution is finished. Its purpose is detection, not final scoping. Later nodes still need to resolve identity and target scope more precisely.

### Candidate Retrieval

Candidate retrieval is intended to narrow the set of existing profiles relevant to a detected subject before identity resolution happens.

The working assumption is that this node can use a mix of:

- exact-name matching
- alias matching
- heuristics
- embeddings / semantic retrieval

The important design decision here is that retrieval should narrow candidates, not finalize identity by itself.

### Identity Resolution

Identity resolution is its own node because matching a mention to an existing profile is a different problem from extracting fields or creating updates.

The working methodology for this node is:

- retrieve a small candidate set from `existing`
- include a `none_of_the_above` option
- compare the detected subject mention against only those candidates
- classify into one of:
  - `unambiguous_existing`
  - `ambiguous_match`
  - `definitely_new`
  - `needs_user_clarification`

This node is one of the most important architectural boundaries in the whole system.

### Human-in-the-Loop for Ambiguity

The architecture now assumes that ambiguity should be handled explicitly and early rather than buried later in extraction or patching.

The human-in-the-loop path is used when the system cannot safely resolve who a message refers to.

A major conclusion from the discussion was that unresolved or ambiguous items should not conceptually force all other resolved work to wait forever. This is what pushed the architecture toward thinking in terms of independent item-level work rather than one giant perfectly synchronized graph run.

Another important reminder is that human-in-the-loop was discussed at two levels:

- subject disambiguation when the system cannot safely tell who is being referred to
- future clarification for unresolved target cases that are not clean subject matches

These should not be collapsed into one vague “ask the user” concept.

### Target-Scope Classification for Non-Simple Facts

One of the biggest design improvements was recognizing that some profile-worthy facts are not simple facts about one already-resolved person.

The diagram now includes a branch for target-scope classification of these non-simple facts.

The currently recognized cases are:

- fact about one identified subject
- fact about multiple explicitly identified subjects
- fact about a subset of subjects selected by a condition
- fact about all subjects in scope
- new entity linked to a known subject
- fact about a non-subject entity

This branch replaced the earlier weaker notion of “orphan facts” with a more precise idea of target scope.

That wording change matters. The project moved away from talking loosely about “orphan facts” because many such facts are not actually orphaned; they simply target something other than a single already-resolved person.

### Case 5 and Relational Memory Pressure

Case 5, such as “Mario has 4 children,” opened a much bigger architectural question than it first appeared.

This branch raises issues such as:

- when a mention should become a first-class entity rather than just a field
- linked-entity detection
- disambiguation of linked entities
- duplication avoidance
- relationship modeling
- schema evolution

This is one of the main gateways from a single `UserProfile` memory model toward a more relational memory model.

The diagram intentionally marks this branch as incomplete because the project does not yet have a final answer here.

### Case 6 and Non-Subject Entities

Case 6 captures facts that are really about some other entity, for example a company, rather than directly about a person.

An example discussed was “Krowdy went bankrupt.”

The important insight was that such a fact should first update or resolve the non-subject entity, and only later may imply downstream effects on people associated with that entity.

This means that a non-subject entity fact should not be treated as if it were already the same thing as a subset-of-subjects update, even if it may later generate one.

### Action Proposal

The action proposal node exists to decide what should happen for resolved subject-scoped items:

- create new profile
- update existing profile
- ignore

This is intentionally separated from identity resolution and also from downstream field extraction or patch generation.

Another useful reminder is that action proposal is only meaningful after identity and target scope are clear enough. If those earlier decisions are unstable, action proposals will inherit that instability.

### Proposal Validator and Proposal Repair

A proposal-level validator was added conceptually to check things such as:

- whether a subject was missed
- whether the chosen identity/action is justified
- whether some ignored item should actually become create/update work

The proposal repair loop exists so the architecture does not rely only on one forward pass. This is not the same as the update-subgraph validator. It is a validator for the proposal set itself.

One clarification reached in the discussion was that this area mostly needs clearer naming and drawing, not a different underlying concept.

### Update Subgraph

The update path in the diagram intentionally preserves the longer deterministic chain:

- `extract_updates`
- `apply_patch`
- `validate`
- `Patch`
- loop back to `validate`
- final commit

This exists because update correctness is considered more sensitive and more structurally constrained than higher-level planning.

The update subgraph is separate from the proposal validator. One validates proposals; the other validates actual patched candidate objects.

### Commit and Canonical State

The diagram assumes a commit step that merges validated `candidate` changes back into canonical `existing`.

The existence of more than one commit box in some diagram revisions was not treated as a conceptual disagreement so much as a drawing clarity issue, because the architecture already assumes reducer-based merging into canonical state.

The important architectural point is that commit is explicit, deterministic, and conceptually separate from validation.

### Fire-and-Forget / Worker Architecture Discussion

One of the most important discussions connected to this diagram was about concurrency and whether the long-term system should use independent item-level workers.

The conclusion was that a truly robust concurrent design should not keep one giant graph execution open while many item-level branches attempt to finish and rejoin.

Instead, the stronger long-term pattern is:

- one orchestration layer analyzes the message and emits item-level tasks
- those tasks are stored durably
- worker runs process them independently
- ambiguous or unresolved tasks become clarification tasks
- slow or broken tasks do not block the rest

This is a real architectural pressure point and should be kept in mind whenever the current monolithic graph starts to feel too synchronized or too fragile.

This discussion should be remembered as unresolved at the execution-model level. The current near-term implementation does not yet use the full worker architecture, but the north-star design increasingly points in that direction for robustness.

### What Was Criticized and Clarified

The latest review of the diagram surfaced several specific criticisms that should be remembered:

- The diagram still risks mixing two execution models: a single long-lived orchestrated run and a more durable task-emission / worker architecture. This is not just a drawing issue. It changes what interrupts, concurrency, and completion mean.
- The non-simple fact branch became much stronger, but some of its labels still risk confusion. In particular, earlier wording around “orphan facts” was weaker than the newer target-scope framing, and future revisions should preserve the more precise target-scope language.
- The handoff from non-simple fact analysis back into the person-centered flow must stay explicit. When a branch eventually feeds back into normal create/update logic, the drawing should make clear what artifact is being handed off rather than relying on visual intuition.
- The proposal validator and the update-subgraph validator must remain conceptually separate. One validates whether the right subjects and actions were chosen; the other validates whether patched candidate objects are structurally and semantically valid. These should never collapse into one vague “validation” idea.
- Case 5 and Case 6 are not equally mature, even if both are intentionally incomplete. Case 5 is clearly marked as a gateway into relational memory and linked-entity modeling. Case 6 is more operationally described, but still hides unresolved questions about how non-subject entity updates should later propagate to affected subjects.
- Several remaining weaknesses are about clarity of text and diagram layout rather than fundamental conceptual disagreement, but that still matters: ambiguous labels can cause future architectural confusion even when the underlying idea is sound.

One more concrete reminder: if the diagram starts to feel contradictory in the future, first check whether the contradiction comes from execution-model assumptions rather than from the memory logic itself. A number of tensions in the review came from mixing “single run with branches” and “durable task plus worker” thinking inside the same picture.

### Practical Reminder for Future Work

When returning to `memory_agent.drawio.xml` later, do not treat every unresolved branch as something that must be solved before continuing implementation.

Instead, treat the diagram as a map of:

- what the current implementation already approximates
- what the near-term plan should progressively move toward
- what the long-term architecture will need once the `UserProfile`-only memory model starts expanding into relational memory, richer validation, and more independent work execution

The file is therefore both:

- a north-star system design
- and a reminder of where the hard unsolved questions still are
