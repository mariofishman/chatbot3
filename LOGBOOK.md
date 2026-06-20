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

## 📋 Log Entry: April 13th, 2026 - Planner Test Baseline and State Split

### Planner Testing Reached a Usable Baseline

The current `planner_node` was tested locally through `src/test_planner.py` instead of only through Studio.

This was important because it created a faster loop for checking whether planner outputs make sense before moving deeper into the refactor.

The planner passed a small baseline set of tests covering:

- create-only cases
- update-only cases
- mixed create/update cases
- interest-only updates
- no-op messages
- multiple new people in one message

An ambiguity test with two existing subjects sharing the same name was also added, but it was explicitly treated as exploratory rather than a pass/fail gate. The current planner can sometimes describe ambiguity in `reasoning_summary`, but it does not yet have an explicit ambiguity field in `PlannerOutput`, so this case should not block progress at the current stage.

### State Boundary Decision Clarified

One important implementation decision was clarified before moving to the next step of the short-term plan: the project should no longer keep one large shared working state for every part of the system.

Instead, the architecture should move toward three different state models:

- one main graph state
- one extract subagent state
- one update subagent state

The reasoning was:

- top-level `messages` should only receive compact summary messages at commit time, not the full internal chatter of subagents
- top-level `existing` remains the canonical shared memory and therefore needs merge semantics
- `candidate`, `errors`, `attempts`, and `patches` are better treated as local working fields inside extract/update workflows rather than as part of the main planner/router state

This decision was written into `src/SHORT_TERM_PLAN2.md` because it directly changes the near-term implementation order.

### Reducer and Merge Logic Clarified Further

Another important clarification was that not every field that may conceptually receive updates should be solved with the same mechanism.

For top-level `messages`, the project should not reduce all internal subagent messages back into the main conversation state, because that would pollute context and make future planning worse. Instead, only a compact summary of what a subagent committed should be appended at commit time.

For top-level `existing`, some kind of merge logic is definitely required because multiple create/update branches may eventually commit into the same canonical store. The key point here is that `existing` should not be overwritten wholesale by a subagent result. It should be merged deterministically by id so that committed updates and committed new profiles can coexist safely.

At the same time, this merge concern helped reinforce the decision to keep working fields such as `candidate`, `patches`, `errors`, and `attempts` out of the main state. Those fields belong inside subagent-local workflows, where retries and validation loops can happen without leaking intermediate state into the top-level graph.

### Practical Consequence

The short-term plan now treats step 5 not only as a reducer question, but as a state-boundary question.

The next implementation work should therefore begin by aligning code with these state boundaries before going further into the create/update subagent refactor.

## 📋 Log Entry: April 17th, 2026 - Step 6 State Models and Step 7 Extract Clarified

### State Models Moved Into `src/state.py`

The state definitions were separated out of `graphv2.py` and moved into `src/state.py`.

At this stage, three state models were defined for the near-term architecture:

- `MainState`
- `ExtractAgentState`
- `UpdateAgentState`

`ExtractionState` was intentionally kept as a transitional legacy state and marked with a comment so the ongoing refactor can happen incrementally rather than all at once.

One useful clarification from this step was that `ExtractAgentState` does not need extra working fields yet in the simple implementation, because the extract flow is still expected to run as a small single-node operation and can use local variables internally.

### Extract Step Was Clarified Further

The short-term plan for step 7 was made more explicit.

For the simple version, `extract` should:

- receive `messages`, `existing`, and `plan`
- use structured output to extract one or more new `UserProfile` objects
- compare the extracted count against `plan.new_person_count`
- retry once if the counts do not match
- return only newly created profiles keyed by fresh ids

This means the simple extract path is committing in the same node rather than introducing a separate commit node inside the extract branch.

### Reducer Logic for Extract Was Clarified

The extract branch will rely on reducer-style merging at the top-level `existing` field.

The important decision here was that extract should not return the full merged `existing` dict. Instead, it should return only the new profiles, and the top-level merge logic should combine them safely with canonical `existing`.

This keeps the simple version aligned with the earlier decision that `existing` is the canonical shared store and should be merged deterministically by id.

### Mismatch Handling Was Upgraded to Human-in-the-Loop

An important improvement to step 7 was made after clarifying what should happen if planner and extractor still disagree after one retry.

Instead of failing closed permanently, the short-term plan now includes a dedicated follow-up step for this case:

- do not commit anything if the planner/extract count still mismatches
- surface the mismatch explicitly
- ask the human for clarification
- then route back into the create path with the additional information

This means the create path now has an explicit human-in-the-loop recovery path rather than silently guessing which count was correct.

## 📋 Log Entry: April 19th, 2026 - Planner Schema Experiment Before Updating `graphv3.py`

### Why We Tested a New Planner Schema

Work paused here while exploring whether the planner should continue returning the old `PlannerOutput` contract or move to a more useful message-selection contract for the new architecture.

The motivation was practical: the old planner output could say how many new people and which existing ids to update, but it did not tell downstream nodes which messages actually contained the relevant information. Since both `extract` and `extract_updates` need tighter context control, a more message-aware planner output started to look like a better fit.

### What Was Tested

A dedicated test file, `src/test_plannerv2.py`, was used to experiment with a richer planner schema without changing `graphv3.py` too early.

The tests explored whether a structured model could:

- receive human messages with explicit ids
- return those same message ids in structured output
- separate create-relevant messages from update-relevant messages
- support the case where one message is relevant for both create and update
- support a message that updates multiple existing profiles
- support a message that introduces multiple new people

These tests mattered because they were not only about prompt wording. They were also about finding a schema shape that OpenAI provider-native structured output would actually accept.

### What Was Learned

The experiments confirmed two important things.

First, the message-selection idea is useful. It gives the planner a better contract for downstream routing because it identifies not only what should happen, but also where in the conversation the supporting evidence lives.

Second, provider-native structured output rejected arbitrary-key dictionary fields such as `dict[str, list[str]]` and `dict[str, int]` in this context. This forced the schema toward a safer list-of-typed-objects design instead.

That led to:

- `UpdateLink`
- `CreateLink`
- `MessageSelectionOutput`

with branch-specific reasoning summaries and typed link objects rather than free-form dictionaries.

### State Schema Was Improved

`src/state.py` was updated to include the improved planner-side schema components:

- `UpdateLink`
- `CreateLink`
- `MessageSelectionOutput`

This newer schema is now documented in the state file and is increasingly looking like the better long-term replacement for `PlannerOutput`.

`PlannerOutput` was intentionally kept for the moment and marked as legacy, because `graphv3.py` has not yet been switched over.

### Where Work Stopped

Work stopped just before improving `planner_node` in `src/graphv3.py`.

That is the next concrete step:

- update `graphv3.py` so the planner uses `MessageSelectionOutput`
- update the planner prompt accordingly
- then make `extract` and `extract_updates` consume the improved planner output rather than the older count-and-target contract

## 📋 Log Entry: April 23rd, 2026 - `graphv3` Create Path Working in Early Form

### `graphv3.py` Was Moved Forward to the New Planner Contract

Work resumed in `src/graphv3.py` using the newer planner-side schema:

- `MessageSelectionOutput`
- `CreateLink`
- `UpdateLink`

The planner node now returns message-selection output rather than the older count-and-target-only schema. This made it possible for downstream create logic to focus only on the human messages the planner marked as relevant.

### Reducer-Based Create Commit Was Put in Place

The top-level `existing` field in `MainState` now uses merge semantics so that the create path can return only newly created profiles keyed by fresh ids.

This was an important implementation checkpoint because it aligns `graphv3` with the short-term plan:

- `extract` should not return the full merged `existing` store
- `extract` should return only newly created profiles
- the canonical top-level `existing` store should absorb those committed profiles through merge behavior

### Early `extract` Contract Was Implemented

An early version of `extract_node` was added in `src/graphv3.py`.

In this temporary version, `extract` now:

- reads `state.plan.relevant_for_create_links`
- narrows itself to the planner-selected create-relevant human messages
- includes the planner's create-side reasoning summary in the extract prompt
- calls structured output with `UserProfileList`
- returns only newly created profiles keyed by fresh UUID strings

This is still an early version because it does **not** yet do:

- planner/extract count consistency checking
- retry on mismatch
- explicit mismatch result handling
- human clarification routing

### Create-Only End-to-End Test Was Run Successfully

A new test file, `src/test_plannerv3.py`, was created to test graph behavior rather than planner output in isolation.

The tested case was a simple create-only message:

- `"I met Lucia Romero, a startup lawyer from Lima."`

The test confirmed that the following path now works in `graphv3`:

- planner
- route
- extract
- reducer merge into top-level `existing`

The result showed that:

- the planner selected the correct human message id
- `extract` focused on that selected message
- the model returned one `UserProfile`
- the new Lucia Romero profile was merged into canonical `existing`
- the previous existing profiles remained intact

This is the first working end-to-end checkpoint for the create branch in `graphv3`.

### Legacy Compatibility Was Intentionally Kept

`PlannerOutput` was not removed from `src/state.py` because `src/graphv2.py` still uses the older `ExtractionState` path.

This was treated as acceptable for now so the new `graphv3` work could continue without prematurely breaking the older frozen baseline.

### Where Work Stopped

Work stopped with the create-only branch functioning in an early form, but without mismatch handling yet.

### Next Steps

The next implementation steps should be:

- add a planner/extract count check inside `extract_node`
- compute the expected create count from `plan.relevant_for_create_links`
- compare that expected count against the number of extracted `UserProfile` objects
- retry extraction once when the counts do not match, with an extra prompt note describing the mismatch
- if the retry still mismatches, return an explicit create-path mismatch result instead of committing anything into `existing`
- define the simple human-clarification path for that mismatch result, following step 7a in `src/SHORT_TERM_PLAN2.md`

After that, the next major phase should be:

- begin the update branch refactor in `graphv3`
- make `extract_updates` consume only planner-selected update-relevant messages and target ids
- keep patch application and validation as deterministic update-local steps

## 📋 Log Entry: Week of April 27th, 2026 - Create Subgraph Clarified and Parent/Subgraph Skeleton Refactored

### This Entry Covers Several Short Work Sessions

Work during this period happened across multiple shorter sessions rather than one continuous implementation block.

Because of that, this entry is written as a weekly summary rather than a single-day checkpoint.

### Create Path Was Extended Beyond the Early Happy Path

The create-side flow in `src/graphv3.py` was pushed beyond the original simple success case.

At this stage, `extract_node` now does more than one-pass extraction:

- it narrows itself to planner-selected create-relevant messages
- it computes the expected create count from `plan.relevant_for_create_links`
- it compares the expected count against the number of extracted `UserProfile` objects
- it retries extraction once with explicit corrective feedback when the counts do not match

This moved the create branch much closer to the intended step-7 behavior from `src/SHORT_TERM_PLAN2.md`.

### The Human Clarification Path Was Implemented With a Different Design Than the Original Plan

The original short-term plan said that after a persistent create mismatch, the human clarification should route back into the create path so `extract` could try again with additional information.

During this week, a different design was chosen and accepted as the new working direction:

- if extraction still mismatches after one retry, `extract_node` routes to a human clarification node
- the human does not provide free-form clarification for `extract` to interpret again
- instead, the human supplies the corrected `UserProfileList` payload directly
- the human correction is treated as authoritative

This means the create mismatch recovery path now works more like:

- model attempts extraction
- model retries once with planner-guided correction
- if still wrong, human directly fixes the extracted structured result

This is simpler and more deterministic than the original route-back-through-extract version, even if it is less user-friendly than a future UX-oriented solution might be.

### Human Interrupt and Resume Contract Was Clarified

The create subgraph now includes a human clarification node using `interrupt(...)`.

An important design clarification was reached here:

- the resume payload should be JSON-serializable
- the expected shape should match `UserProfileList`
- the human node should validate the resumed payload with `UserProfileList.model_validate(...)`

A retry loop was then added around this validation so that invalid human payloads do not crash the run immediately.

Instead:

- the graph interrupts with the first clarification prompt
- if the resumed payload does not match `UserProfileList`, the graph interrupts again with validation errors and an example payload shape
- this repeats until the payload validates

This created the first concrete interrupt/resume flow in `graphv3.py`.

### A New Architectural Clarification Was Reached About Main Graph vs Subgraphs

A major conceptual clarification happened during this period.

The earlier `graphv3.py` iterations were still implicitly flattening create/update logic into one graph, even though the intended architecture had already moved toward separate subagents with their own states.

That was corrected conceptually:

- `MainState` belongs to the parent graph
- `ExtractAgentState` belongs to the create subgraph
- `UpdateAgentState` belongs to the update subgraph
- the parent graph should call compiled subgraphs rather than host all internal create/update nodes directly

This was an important architectural checkpoint because it confirmed that the issue was not “different states are confusing,” but rather “the graph boundaries must match the state boundaries.”

### Skeleton Refactor Began for Parent Graph and Subgraphs

Work then shifted from only refining `extract_node` to sketching the full graph structure.

`src/graphv3.py` now contains a skeleton for:

- the create subgraph
- the update subgraph
- the parent graph
- wrapper nodes that invoke the subgraphs from the parent graph

This skeleton is still incomplete in the update branch, but it captures the intended architecture more faithfully than the earlier versions.

### Parent Routing Was Clarified Further

The parent graph should route after the planner based on the planner output:

- to the create subgraph if `relevant_for_create_links` is non-empty
- to the update subgraph if `relevant_for_update_links` is non-empty
- to both in parallel if both are non-empty
- to `__end__` if neither branch is needed

An important clarification here was that this parent-level fan-out is better expressed with `add_conditional_edges(...)` returning multiple destinations, rather than trying to use `Command` for the planner.

At the same time, `Command` remained appropriate inside the create subgraph, where one node both updates subgraph state and chooses whether to route to human clarification or to finish.

### `SHORT_TERM_PLAN3.md` Was Added

A new file, `src/SHORT_TERM_PLAN3.md`, was created as a holding place for improvements that go beyond the “simple version” in `src/SHORT_TERM_PLAN2.md`.

This was done because several ideas emerged that were clearly useful, but were no longer part of the near-term minimal path:

- create-side validation stronger than count-only checking
- more targeted repair of missing/extra/merged/split extracted people instead of full regeneration
- a better planner prompt/context strategy so the planner does not always receive all messages and all existing profiles as memory grows

This kept `SHORT_TERM_PLAN2.md` focused while preserving the next-wave architectural ideas.

### Step 7 / 7a Was Reinterpreted and Treated as Complete

After discussion, the create-path work was treated as complete enough for steps `7` and `7a`, with one important caveat:

- the implementation now satisfies the spirit of create mismatch handling
- but it does so through human-supplied structured correction rather than by routing human clarification back into `extract`

This was accepted as the new short-term design.

### Where Work Paused

Work paused just before beginning the real implementation of the update subgraph.

The update branch skeleton exists, but its internal logic is still mostly placeholder code.

### Next Steps

The next implementation move should be:

- begin step `8` in earnest by implementing `update_patches` / `extract_updates`
- make the update subgraph consume only the planner-selected update slice, not the full parent context
- narrow update-side inputs so the update branch receives:
  - only update-relevant messages
  - only the target ids selected by the planner
  - only the matching existing profiles for those ids

## 📋 Log Entry: May 3rd, 2026 - Wrapper Filtering Moved Into the Parent Graph and Subgraph Contracts Tightened

### The Focus Shifted From Create Logic To Subgraph Input Contracts

After the April 27th checkpoint, the work did not move straight into implementing `update_patches`.

Instead, the next round of work clarified something more foundational first:

- what each subgraph should actually receive as input
- which filtering should happen in the parent wrappers
- which assumptions the subgraph nodes are allowed to make

This turned out to matter because the architecture was already pointing toward create and update subgraphs, but the actual data boundaries were still too loose.

### Create-Side Filtering Was Moved Out of `extract_node`

One of the main changes was to stop making `extract_node` discover its own relevant messages from the full parent state.

That responsibility was moved into the parent wrapper `run_extract_subgagent(...)`.

The create wrapper now:

- reads `plan.relevant_for_create_links`
- extracts only the matching human messages
- builds a narrowed `MessageSelectionOutput`
- invokes the extract subgraph with only the create-relevant slice

As a result, `extract_node` is now simpler and cleaner:

- `state.messages` is assumed to already contain only create-relevant messages
- the node no longer needs to filter message ids internally before building its prompt
- it still uses the create-side planner summary and create-count information from `state.plan`

This made the create subgraph contract much clearer.

### Update-Side Filtering Was Also Moved Into Its Parent Wrapper

The same narrowing decision was then applied to `run_update_subgagent(...)`.

The update wrapper now filters both:

- `messages`, using `plan.relevant_for_update_links`
- `existing`, using the user-profile ids attached to each update link

This means the update subgraph no longer needs to receive the full parent context in order to begin working.

Inside the update subgraph:

- `messages` now means “already filtered update-relevant messages”
- `existing` now means “already filtered target profiles selected by the planner”

This preserves the original field names while changing their scope inside the subgraph.

### Narrowed Planner Objects Are Now Passed Into Each Subgraph

Another important refinement was made to the `plan` field.

Rather than passing the full planner output unchanged into both subgraphs, each wrapper now builds a fresh `MessageSelectionOutput` instance that keeps only the branch-relevant fields:

- the create wrapper keeps create-side fields and clears update-side fields
- the update wrapper keeps update-side fields and clears create-side fields

This avoided mutating the parent `state.plan` in place and made each subgraph receive a more honest branch-local planner object.

This was an important cleanup because earlier attempts were accidentally modifying or over-sharing planner data.

### The Human Clarification Loop Remained in Place, but the Contract Became More Explicit

The human node inside the create subgraph still follows the same short-term design chosen earlier:

- on persistent mismatch, the human provides the corrected structured result directly
- the result must match `UserProfileList`
- invalid payloads trigger another interrupt with validation guidance

What became clearer during this phase is that this is now a real subgraph contract, not only an implementation detail:

- the create subgraph may finish through direct extraction success
- or it may finish through authoritative human-supplied structured correction

That contract is now consistent with the rest of the create subgraph architecture.

### `SHORT_TERM_PLAN2.md` Was Updated Again To Match the Real Design

Several plan clarifications were written into `src/SHORT_TERM_PLAN2.md` so that the document matches the current implementation direction more closely.

The main changes were:

- step `7a` now explicitly reflects the accepted short-term human-fix design
- step `9` now explicitly says filtering should happen in the parent wrappers
- the plan now states that subgraphs keep the same field names (`messages`, `existing`) while receiving already-filtered branch-local context
- the plan now states that `extract_node` should assume create-filtered messages and the update path should assume update-filtered messages and profiles

This matters because the plan is no longer only aspirational; it now records several concrete architectural decisions that were already implemented.

### Current State of `state.py`

At this checkpoint:

- `MainState` still carries the canonical top-level fields:
  - `messages`
  - `existing`
  - `plan`
- `ExtractAgentState` extends this with create-specific mismatch and human-interaction fields
- `UpdateAgentState` still holds the update-side working fields for candidate state, errors, attempts, and patches

An important practical conclusion was accepted during this period:

- a subgraph may keep `existing` in its state schema even if it does not use the full parent `existing` as input
- the important distinction is between the field name and the scope of the data passed into it

This kept the state models workable without forcing a premature state redesign.

### Current State of `graphv3.py`

By the end of this work period, `graphv3.py` reflects the architecture more faithfully than before:

- the extract subgraph is active and has a clearer input contract
- the update subgraph skeleton exists but still contains placeholder internal nodes
- the parent graph now does more of the filtering and branch preparation work it was supposed to own
- the wrappers now behave more like real boundary adapters between the parent graph and the subgraphs

This is a meaningful architectural improvement even though the update logic itself is not implemented yet.

### Where Work Paused

Work paused after finishing the wrapper-level filtering and branch-specific planner narrowing.

At this point:

- the create branch is cleaner and more self-consistent
- the update wrapper now prepares filtered subgraph inputs
- the update subgraph still needs its first real implementation step

### Next Steps

The next implementation move should be:

- begin implementing `update_patches(...)` as the first real update-subgraph node
- make it consume the already-filtered `messages`, already-filtered `existing`, and narrowed update-side `plan`
- then continue with the deterministic update flow:
  - `apply_patch`
  - `validate`
  - `route_patches`
  - `patch`
  - `commit`

After that:

- implement `apply_patch`

## 📋 Log Entry: Week of May 11th, 2026 - Update Branch Refactored Toward Per-User Send Fan-Out

### The Main Architectural Shift This Week Was About Update Granularity

After the May 3rd checkpoint, the focus stayed on the update branch, but the most important change was not yet writing `update_patches(...)`.

Instead, the key architectural question became:

- should one update subgraph run try to update several existing profiles at once
- or should the parent graph fan out one update run per target `user_id`

The latter direction was chosen.

This was an important shift because it changes the shape of the update branch from:

- one batched update wrapper receiving several profiles at once

to:

- one parent-side fan-out step
- many per-user update wrapper calls
- one update subgraph run per target profile

### Why Per-User Update Fan-Out Was Chosen

The main reason for this refactor was to reduce model confusion.

When one LLM call sees several existing profiles and several update-relevant messages together, it is easier for the model to:

- mix up which update belongs to which person
- apply information from one message to the wrong profile
- produce patch proposals that are harder to inspect or debug

By splitting the update work one target profile at a time, each update run can focus on:

- one `user_id`
- one existing `UserProfile`
- only the messages relevant to that profile

This should make the later update prompts simpler, the model behavior cleaner, and the debugging surface smaller.

### The Parent Graph Now Owns Update Fan-Out

Another architectural clarification happened during this period.

At first, there was some ambiguity about where the update fan-out should live:

- inside the update subgraph
- or in the parent graph

The chosen direction is now:

- the parent graph owns the update fan-out

This fits the current wrapper-based architecture better because the parent graph is already responsible for:

- receiving the planner output
- deciding which branches to run
- preparing branch-specific payloads
- invoking subgraphs

So the update splitting decision now lives at the same architectural level as the rest of the branch orchestration.

### `Send` Became the Chosen Mechanism for Per-User Update Parallelism

The update branch is now being refactored around LangGraph’s `Send` API.

The important idea here is:

- the planner still decides which existing users need updates
- but after that, the parent graph can dynamically create one parallel branch per relevant `user_id`

This allows the update branch to move toward a map-reduce style pattern:

- map:
  - one `Send(...)` per user profile that needs updating
- reduce:
  - partial `existing` updates merge back through reducers

This refactor is still incomplete at the node-logic level, but the graph shape now reflects that direction much more clearly.

### `fan_out_updates(...)` Was Introduced As a Helper for Per-User Grouping

A new helper was introduced in `graphv3.py` to regroup planner output by user.

The planner still produces `relevant_for_update_links` in message-oriented form:

- one message id
- one or more `user_profile_ids` that should be updated from that message

The new helper turns that into a user-oriented grouping:

- one `user_id`
- all message ids relevant to that user

This matters because one user may be mentioned in multiple messages, and one message may mention multiple users.

So the update branch now moves toward the right per-user payload shape:

- `existing`: one target profile
- `messages`: all update-relevant messages for that profile
- `plan`: still available for wrapper-level access where needed

### The Router Was Reworked So Update Fan-Out Happens Directly After Planning

The parent router was also reconsidered.

An important clarification was reached:

- a routing function can return `Send(...)` objects
- but a routing function is not itself a graph node
- so there cannot be a “router after a router” unless a real node sits between them

Because of that, the cleaner solution for the current design became:

- keep `planner` as the real parent node
- keep a single `route_after_planner(...)`
- let that router directly:
  - append `"extract_subagent"` when create work exists
  - extend with `fan_out_updates(state)` when update work exists
  - return `["__end__"]` when neither branch is needed

This removed the need for a fake or no-op fan-out node and kept the routing logic closer to the expert-style `Send` examples from the LangGraph docs.

### `UpdateAgentState` Was Narrowed Further

Another change during this period was a reconsideration of update-side state boundaries.

`UpdateAgentState` was changed so it no longer simply inherits everything from `MainState`.

The update subgraph now has a narrower state model focused on what one per-user update run actually needs:

- `messages`
- `existing`
- `reasoning_summary_for_update`
- update-local working fields such as `candidate`, `errors`, `attempts`, and `patches`

This is an important step because the update subgraph no longer conceptually represents “all update work for the turn.”

It now represents:

- one update run for one existing target profile

### A Practical Compromise Was Kept Around `reasoning_summary_for_update`

One open design issue during this period was how much to narrow the planner summary text for each per-user update run.

The broad planner field:

- `reasoning_summary_for_update`

may mention several users at once.

A stricter design would try to generate or derive one summary per target user.

That was considered unnecessary for now.

The accepted short-term compromise is:

- keep passing the shared update summary text
- rely primarily on the already-filtered `messages` and one-user `existing`
- treat the shared summary only as loose background information

This keeps the refactor smaller while still benefiting from the per-user fan-out architecture.

### The Result Is A Cleaner Shape Even Before `update_patches(...)` Is Written

At the end of this week, the update branch is still not implemented internally, but its outer structure is much clearer:

- the planner selects update-relevant work
- the parent router can fan that work out one user at a time
- each update wrapper call is now conceptually responsible for one profile only
- the update subgraph state is narrower and more local than before

This is a meaningful improvement because it should make the next implementation steps inside `update_subgraph` easier and less error-prone.

### Where Work Paused

Work paused after the per-user `Send` refactor was made coherent enough to test.

At this point:

- the update branch shape has changed significantly
- the create branch remains as previously stabilized
- the internal update nodes are still placeholders

### Next Steps

The next implementation move should be:

- test the new planner -> `route_after_planner(...)` -> per-user `Send(...)` fan-out -> `run_update_subgagent(...)` path before writing update logic
- confirm that each update wrapper call receives the intended one-user payload
- only then begin implementing:
  - `update_patches(...)`
  - `apply_patch(...)`
  - `validate(...)`
  - `route_patches(...)`
  - `patch(...)`
  - `commit(...)`

## 📅 Log Entry: Sunday, May 17th, 2026 - Update Fan-Out Architecture Tested Before Writing Update Logic

### A Dedicated Architecture Test Was Added For The New Update Branch Shape

Before starting to implement the internal nodes of `update_subgraph`, a new test file was added to validate only the update fan-out architecture that had just been refactored.

The new file is:

- `src/test_update_fanout_v3.py`

Its purpose is not to test `update_patches(...)` or patch logic yet.

Instead, it tests the graph shape that now exists around the update branch.

### What The New Test Verifies

The new test file verifies three things:

1. `fan_out_updates(...)` correctly regroups planner-selected update work by `user_id`
2. `route_after_planner(...)` correctly returns a mixed result containing:
   - `"extract_subagent"` when create work exists
   - one `Send(...)` per target update user
3. `run_update_subgagent(...)` correctly receives one-user payloads and builds the narrower `sub_state` that will later be passed into `update_subgraph`

This was an important checkpoint because the update branch had just been significantly refactored, but the real update-subgraph node logic still did not exist.

### A Fake `update_subgraph` Was Used On Purpose

To keep the test focused on architecture rather than unfinished node logic, the test temporarily replaces the real `update_subgraph` with a fake object.

That fake object simply captures the payload passed into `update_subgraph.invoke(...)`.

This made it possible to inspect:

- whether each `Send(...)` carries the correct one-user `existing`
- whether each `Send(...)` carries only the relevant messages for that user
- whether `run_update_subgagent(...)` passes the expected narrowed fields into the update subgraph boundary

### The Test Passed

The local test run succeeded.

This means the current architecture is now working at the level of:

- planner output
- parent routing
- per-user `Send(...)` fan-out
- one-user wrapper payload construction

That does not yet mean the update branch works end to end, because the internal update-subgraph nodes are still placeholders.

But it does mean the refactor reached a stable enough checkpoint to begin writing the real update logic.

### Why This Was A Useful Pause Point

This test confirmed that the most recent refactor was not only conceptually cleaner, but also mechanically coherent.

In particular, it validated that the project can now move forward with the update branch under this structure:

- one planner decision at the parent level
- one per-user `Send(...)` branch for updates
- one `run_update_subgagent(...)` call per target profile
- one narrower `UpdateAgentState` payload passed into `update_subgraph`

That reduces the risk of writing `update_patches(...)` on top of unstable graph wiring.

### Updated Next Steps

The next implementation move should now be:

- begin writing `update_patches(...)`
- keep it focused on one target profile at a time
- make it consume:
  - one-user `existing`
  - the list of relevant messages for that user
  - `reasoning_summary_for_update` only as supporting context

After that:

- implement `apply_patch(...)`
- implement `validate(...)`
- implement `route_patches(...)`
- implement `patch(...)`
- implement `commit(...)`
- implement `validate`
- implement the update repair/commit loop

## 📅 Log Entry: June 4th, 2026 - Update Subgraph Implemented As A Full Patch-Validation-Repair Loop

### The Internal Update Branch Was Finally Built

Since the previous log entry, the biggest architectural change has been inside `src/graphv3.py`.

The update branch is no longer only a per-user fan-out shell. Its internal nodes now exist and work together as a real loop:

- `update_patches(...)`
- `apply_patch(...)`
- `validate(...)`
- `route_patches(...)`
- `patch(...)`
- `human_repair(...)`
- `commit(...)`

This means the project now has a full update-side path from:

- one selected existing user profile
- one set of update-relevant messages
- one patch proposal cycle
- deterministic patch application
- deterministic validation
- retry routing
- human fallback after retry exhaustion
- final commit back into parent memory

### The Update Loop Became More TrustCall-Like

The update subgraph was clarified around a more precise separation of responsibilities:

- `update_patches(...)` asks the model for patch proposals only
- `apply_patch(...)` applies those patch operations deterministically
- `validate(...)` reconstructs the raw candidate as `UserProfile` and turns reconstruction failures into `state.errors`
- `route_patches(...)` decides whether to:
  - commit
  - retry with `patch(...)`
  - or hand off to `human_repair(...)` after the attempt limit
- `patch(...)` asks the model for corrective patches using the failed candidate plus validation errors
- `human_repair(...)` preserves state and interrupts for human-provided patch proposals
- `commit(...)` rebuilds the final `UserProfile` and returns only the one-user `existing` slice

This is important because the project is no longer mixing:

- patch generation
- patch application
- validation
- retry decisions
- final merge

inside the same step.

### `state.py` Was Simplified Around The New Contract

The state layer was also tightened to match the new update design.

The most important change is that `UpdateAgentState.candidate` is now raw patched dict data, not a `UserProfile` object.

That allows:

- `apply_patch(...)` to stay deterministic
- `validate(...)` to own schema reconstruction
- `state.errors` to become the true repair signal for the retry loop

Also, `merge_profiles(...)` was clarified and constrained:

- it now exists only as a dict-level reducer by `user_id`
- it keeps missing ids
- adds new ids
- replaces whole `UserProfile` objects on collision
- it does not merge fields inside a profile

That field-level work now belongs clearly to the update subgraph before commit.

Legacy state structures that only served the old `graphv2` path were removed from `state.py`.

### Human Repair Was Added Instead Of Hard Failure

One important architectural decision changed during implementation.

Originally, retry exhaustion in `route_patches(...)` was treated like a hard runtime failure.

That was replaced with a better design:

- after the patch-attempt limit is reached
- the graph routes to `human_repair(...)`
- `human_repair(...)` uses `interrupt(...)`
- the human returns a `PatchProposalList`
- the graph goes back through:
  - `apply_patch(...)`
  - `validate(...)`

This preserves state instead of losing it through an exception, which is a better fit for the project.

### The New Update Logic Is Now Protected By Tests

The new architecture is not only implemented; it is also covered by focused tests.

The update-side and state-side tests added in this phase include:

- `tests/test_update_patches_v3.py`
- `tests/test_apply_patch_v3.py`
- `tests/test_validate_v3.py`
- `tests/test_route_patches_v3.py`
- `tests/test_patch_v3.py`
- `tests/test_human_repair_v3.py`
- `tests/test_commit_v3.py`
- `tests/test_state_reducers_v3.py`

Together with the earlier:

- `tests/test_update_fanout_v3.py`
- `tests/test_route_after_planner_v3.py`

the codebase now has meaningful regression protection around the current live architecture.

### Repository Cleanup Also Happened During This Phase

While the update loop was being implemented, the repository was also cleaned up:

- legacy tests were moved out of `src/`
- the active test suite was moved into `tests/`
- old simpler code was moved into `old_project/`
- deprecated graph v2 artifacts were separated from the live path
- microplans were centralized under `microplans/`

This makes the active codebase much easier to read:

- live runtime code is mainly in `src/graphv3.py` and `src/state.py`
- tests are in `tests/`
- implementation planning notes are in `microplans/`

### Current Stage

The update subgraph is now implemented at the node level and tested at the unit level.

This is a major shift from the previous checkpoint, where only the outer update fan-out shape had been verified.

The current architecture now supports:

- planner-driven create/update separation
- one-user-at-a-time update fan-out
- patch generation
- deterministic patch application
- validation-driven retry
- human repair fallback
- committed whole-profile replacement in parent state

### Likely Next Step

The next strong checkpoint would be:

- one integration test for the full update subgraph retry loop

That would verify the whole sequence:

- `update_patches`
- `apply_patch`
- `validate`
- `route_patches`
- `patch`
- `human_repair` when the retry limit is exhausted
- `commit`

under one controlled end-to-end scenario.

## 📅 Log Entry: January 4th, an architectural problem was found

While trying to design the mixed create-and-update integration path, a real limitation appeared in the current batch-planning architecture.

The problem is not in the update subgraph itself. The problem is earlier, in the way the create side currently represents new people across multiple messages.

Right now, create planning works with `CreateLink(message_id, new_person_count)`.

That means the system can say:

- this message is relevant for creating new people
- this message contains `N` new people

But it cannot say:

- this later message is about the same new person already mentioned in an earlier message

That became visible in the following kind of case:

- one shared message mentions:
  - a new person
  - another new person
  - and one already known person
- a later message adds more information about one of the new people
- another later message updates the already known person

Example:

- `hm_001`: "I met Lucia Romero from Lima and Diego Salazar from Bogota. Philip de Haas is now based in Zurich."
- `hm_002`: "Lucia Romero is a startup lawyer."
- `hm_003`: "Philip de Haas also works often from Geneva."

In the current architecture:

- `hm_001` can say `new_person_count = 2`
- but `hm_002` has no way to say:
  - "this is not a second new person"
  - "this is more evidence about Lucia from `hm_001`"

So if both messages are treated as create-relevant, the create side counts too many new people.

This revealed an important architectural fact:

- the current update path is able to accumulate multiple messages for one known user because it has stable `user_id`s
- the current create path does not yet have an equivalent notion of stable temporary person identity inside one batch

So the mixed create+update test did not fail because the test was bad.

It failed because the test exposed a real missing capability in the planner/extraction architecture.

### What We Are Thinking Of Doing

Two directions were considered.

#### Option 1: Run The Whole Parent Flow One Message At A Time

This would mean:

- process message 1
- update `state.existing`
- process message 2 with the new memory
- process message 3 with the newer memory

This would solve the identity problem with relatively little architectural change.

But it likely makes token usage and latency much worse, because the whole parent flow would run once per message.

#### Option 2: Add A Batch-Level Person Grouping Stage

This is the direction that currently looks more promising.

The idea would be:

- loop over the incoming human messages
- identify people mentioned in each message
- maintain temporary per-person buckets for the current batch
- if a person mentioned in a later message matches a person already discovered in the batch, add the new evidence to the same bucket
- only after that grouping step, decide:
  - which buckets match existing users and should go to update
  - which buckets are truly new and should go to create

That would let repeated mentions of Lucia across multiple messages accumulate into one create candidate without rerunning the whole graph one message at a time.

### Why This Matters

This is a bigger issue than one failing integration test.

It means the current planner schema is still good enough for:

- create-only messages
- update-only messages
- batch updates for already known users

But it is not yet rich enough for:

- mixed create+update batches where new people are mentioned repeatedly across messages before they have final ids

So the next architectural work is not just "finish one more test."

The next architectural work is to decide how the system should represent new-person identity across a batch before those people become committed profiles.

# Project Logbook Part 3 - Subject Identity Refactor

## 📅 Log Entry: June 7th, 2026 - Architectural problem confirmed and next refactor direction chosen

This entry marks the beginning of a new phase of the project.

The work recorded in the earlier parts of the logbook was mainly about getting the current `graphv3.py` architecture built and tested:

- planner
- create path
- update fanout
- update subgraph
- validation / repair loop
- reducers
- unit tests
- parent-path integration tests

That work was successful enough that the codebase could finally be tested against stronger mixed-path scenarios rather than only simpler create-only or update-only cases.

While doing that, a previously suspected limitation became much clearer.

### What Happened Today

Three things happened during this checkpoint:

- the mixed create+update path was analyzed more seriously
- the create-side identity limitation was confirmed as a real architectural issue rather than only a test-design problem
- the next refactor direction was narrowed into a simpler short-term scope plus a separate architecture note

This matters because the project is no longer only extending the current graph.

It is now also deciding which parts of the upstream planner logic should be split out into their own earlier stages.

### Where We Are Coming From

The current architecture was designed around a top-level planner that reads a batch of messages and decides:

- which messages are relevant for create
- which messages are relevant for update

For the create side, the current planner schema is still built around:

- one `message_id`
- one `new_person_count`

That was good enough to get the current architecture off the ground and make the create path work for simpler cases.

But it turns out to be too weak for repeated mentions of the same new person across a batch.

### The Problem That Was Confirmed

The important discovery is that the current create-side planner contract is not rich enough for repeated mentions of the same new person across multiple messages in the same batch.

It works for:

- create-only messages
- update-only messages
- repeated updates to already known users

But it does not let the system express:

- Lucia in message 1 is the same new person as Lucia in message 2
- Diego in message 1 is the same new person as Diego in message 3

At the same time, the update side already has stable `user_id`s and can correctly accumulate multiple messages for one known user through fanout.

So the pressure point is not the update subgraph.
It is the lack of a batch-level subject identity layer before create/update planning.

### Why We Are Moving In A New Direction

One possible fix would have been to run the whole parent graph one message at a time so later messages could see newly committed profiles from earlier messages in the same run.

That would likely solve the identity problem with relatively little code change.

But it would likely make:

- latency worse
- token usage worse
- batching weaker

So that is not the preferred direction.

The preferred direction is now to move the current architecture one step closer to the broader north-star logic described in `memory_agent.drawio.xml`.

### What `memory_agent.drawio.xml` Is

`memory_agent.drawio.xml` is not the current implementation plan.

It is the broader architectural north-star for the project.

It describes a stronger upstream workflow with ideas such as:

- subject and fact detection
- candidate retrieval / filtering
- identity resolution
- action proposal
- earlier human disambiguation when needed

For Part 3, that file is important mainly as a north-star reference.

It explains where the project may grow later, but it does not define the exact scope of the next short-term refactor by itself.

That file became important again because the mixed create+update limitation is exactly the kind of issue that the upstream subject-identification and identity-resolution logic was meant to address.

### What The New Refactor Direction Is

The current short-term conclusion is:

- do not solve this by rerunning the whole parent graph one message at a time
- instead, move the architecture toward:
  - subject detection
  - candidate retrieval / filtering
  - identity resolution
  - action proposal

as a stepping stone toward the broader north-star logic in `memory_agent.drawio.xml`.

More concretely, the next refactor wave should:

- add an upstream subject-identification and identity-resolution stage
- redesign create planning so it becomes person-centric rather than message-count-centric
- only later refactor create execution into one-create-unit-per-person fanout

After the later architecture discussion, that direction was narrowed further for Part 3:

- subject detection: yes
- candidate retrieval: yes
- binary existing/new classification: yes
- ambiguity handling: later
- human clarification for subject identity: later
- full non-simple-fact scope handling: later

### Why This Starts Project Logbook Part 3

This is now `Project Logbook Part 3` because the project is no longer only extending the architecture built in Part 2.

It is beginning a new wave of work:

- not only adding nodes
- but revisiting the upstream subject model itself
- while trying to preserve what already works in `graphv3.py`

So Part 3 marks the start of the subject-identity refactor phase.

The detailed architectural reasoning for this shift is recorded in [ARCHITECTURAL_NOTE.md](/Users/mariofishman/projects/chatbot3/ARCHITECTURAL_NOTE.md).

### Important Memory For Later

If returning to this entry in a future session, remember:

- the current `graphv3.py` architecture is not being thrown away
- the update subgraph and update fanout are still considered solid
- the weak point is upstream from extraction, in the create-side subject representation
- `route_after_planner(...)` is part of the pressure point because it currently routes create work using a message-count-centric planner output
- Part 3 is intentionally conservative:
  - existing vs new only
  - no ambiguity branch yet
  - no identity clarification workflow yet

### Likely Next Step

The likely next implementation step after this entry is:

- define the exact Stage 1 upstream subject-bucket schema in code-facing terms
- then introduce the new upstream node and state fields that support it

## 📅 Log Entry: June 9th, 2026 - Part 3 Steps 1-3 Completed: Upstream Subject Detection Added

The first three executable steps of
[SHORT_TERM_PLAN3v3.md](/Users/mariofishman/projects/chatbot3/src/SHORT_TERM_PLAN3v3.md)
are now complete.

This work created the first concrete layer of the subject-identity refactor
described in the June 7 entry. The parent graph can now identify people across
the received human-message batch before the existing planner runs.

### Step 1: Upstream Subject Schema

`state.py` now defines:

- `SubjectBucket`
- `SubjectBucketList`

One `SubjectBucket` represents exactly one batch-local person and contains:

- the best available subject label
- all supporting human-message IDs
- an optional matching existing-profile ID
- a binary classification:
  - `existing`
  - `new`

The schema enforces that existing subjects have a candidate existing ID and
new subjects do not.

### Step 2: Parent State Extended

`MainState` now carries:

- `subjects: SubjectBucketList`

It defaults to an empty `SubjectBucketList`, allowing the graph to begin before
the upstream node has detected subjects.

The existing profile reducer, update-side state, and update-subgraph contracts
were deliberately left unchanged.

### Step 3: Upstream Subject Node Added

`graphv3.py` now includes `upstream_subject_node(...)`.

The parent graph begins:

```text
START -> upstream_subject_node -> planner
```

The node:

- analyzes the human messages currently received through state
- groups repeated mentions of the same person
- separates multiple people mentioned in one message
- supports unnamed people described through relationships
- compares detected people with `state.existing`
- classifies each person as existing or new
- treats uncertain existing-profile matches conservatively as new
- validates returned message and profile IDs
- retries once when the model returns unknown identifiers

The existing planner and downstream create/update paths remain unchanged for
now. They do not yet consume the new subject buckets; that begins in Step 4.

### Runner And Accumulated-Message Contract

The terminal runner was checked to clarify how repeated passes work.

`playground_run_graph.py` submits only the newly entered human message on each
turn. The checkpointer supplies earlier state, and the additive message reducer
combines prior messages with the new input.

Therefore:

- the upstream node can analyze accumulated conversation history
- earlier messages are not resubmitted by the runner
- message IDs are not duplicated during the intended runner workflow
- the same accumulated history can be analyzed again without mutating it

### Edge-Case And Test Work

The subject-detection behavior was explored in:

- [UPSTREAM_SUBJECT_NODE_EDGE_CASES.md](/Users/mariofishman/projects/chatbot3/microplans/UPSTREAM_SUBJECT_NODE_EDGE_CASES.md)

That document records:

- empty and no-subject inputs
- named and unnamed subjects
- mixed existing/new people
- repeated mentions across messages and turns
- matching and ambiguity boundaries
- state-shape and message-ID boundaries
- retry and structured-output boundaries
- semantic cases that require later live-model evaluation

A focused deterministic test file was added:

- `tests/test_upstream_subject_node_v3.py`

It verifies the node's deterministic contracts, including:

- prompt construction
- subject-bucket shapes
- checkpointed two-turn accumulation
- repeated analysis without message mutation
- existing/new reclassification across passes
- message/profile ID validation
- retry behavior

Verification result:

```text
19 passed
```

### Important Memory For Later

- Subject detection is now separate from planning, but the planner still uses
  the old message-count-based create schema.
- The node is intentionally batch-agnostic: it analyzes whichever accumulated
  messages the graph supplies.
- Binary classification remains intentionally simple and risky:
  - existing
  - new
- Full ambiguity handling, clarification, groups, and stronger identity
  resolution remain future work.
- Deterministic tests can protect node contracts, but they cannot prove that a
  live model will correctly resolve every natural-language identity case.

### Next Step

Proceed to Step 4 of `SHORT_TERM_PLAN3v3.md`:

- redesign `CreateLink`
- redesign the create-side portion of `MessageSelectionOutput`
- replace message-count-based create planning with one create unit per
  identified new person and its supporting message IDs

## 📅 Log Entry: June 9th, 2026 - Architecture Review

After completing Steps 1–3, we recognized that `SubjectBucketList` already
contains the information needed to route both new and existing subjects.
Keeping `planner_node(...)`, `CreateLink`, `UpdateLink`, and
`MessageSelectionOutput` would duplicate that planning information.

`SHORT_TERM_PLAN3v4.md` now supersedes the remaining steps of
`SHORT_TERM_PLAN3v3.md`. It preserves completed Steps 1–3, then migrates both
fanout paths and their consumers before safely removing the old planner
architecture.

## 📅 Log Entry: June 10th, 2026 - Entry 1: Existing-Subject Update Path Migrated

Step 4 of `SHORT_TERM_PLAN3v4.md` migrated the parent graph's update path from
the old planner output to `SubjectBucketList`.

`fan_out_updates(...)` now reads existing-classified subject buckets directly
from `state.subjects`. Each bucket creates one `Send("update_subagent", ...)`
containing exactly one matched existing profile and only that subject's
supporting messages. It no longer reads or sends `state.plan`.

`run_update_subgagent(...)` was adapted to accept this narrower payload and
forward only the selected profile and supporting messages into
`update_subgraph`.

`route_after_planner(...)` is temporarily hybrid during the migration:

- create routing still uses the old planner output
- update routing now uses existing-classified subject buckets

The obsolete update reasoning summary was also removed from
`UpdateAgentState`, `update_patches(...)`, and `patch(...)`. Update proposals
now rely on the selected existing profile and supporting messages; repair
additionally relies on the failed candidate and validation errors.

Future reference commit:

```text
b9fa4821f3072ab6be770ff6edd988c2ce074c53
Migrate update fanout to subject buckets
```

## 📅 Log Entry: June 10th, 2026 - Entry 2: New-Subject Create Path Migrated

Step 5 of `SHORT_TERM_PLAN3v4.md` migrated the parent graph's create path from
the old planner architecture to `SubjectBucketList`.

`fan_out_creates(...)` now reads new-classified subject buckets directly from
`state.subjects`. Each bucket creates one `Send("extract_subagent", ...)`
containing exactly one subject and only the messages that support that subject.
Multiple supporting messages no longer cause multiple extraction branches for
the same person.

The extraction branch was redesigned around this one-subject contract:

- `ExtractAgentState` now carries one subject bucket, its supporting messages,
  and the newly created profile output.
- `run_extract_subgagent(...)` translates the parent branch state into the
  narrower extract-subgraph input and returns a partial parent-state update.
- `extract_node(...)` asks for exactly one `UserProfile` for the supplied
  subject instead of extracting a batch of profiles.
- The old create-count mismatch, retry, and human-interrupt flow was removed
  because each extraction branch now represents exactly one detected subject.
- Created profiles continue returning through the parent `existing` field so
  `merge_profiles(...)` can combine parallel create and update results.

The parent graph now routes both new and existing subject buckets directly
after `upstream_subject_node(...)`. The old `planner_node(...)`,
`MainState.plan`, `CreateLink`, `UpdateLink`, `MessageSelectionOutput`, and
batch-oriented `UserProfileList` schema were removed because
`SubjectBucketList` now provides the routing information they duplicated.

Tests tied specifically to the removed planner, batch extraction, old create
human flow, and previous parent integration contracts were deleted. They must
be replaced with focused Step 5 tests covering create fanout, the extraction
wrapper and subgraph, and parent create/update routing. No replacement tests
were written or run before this commit so the implementation could be preserved
as a clear checkpoint before test development begins.

Future reference commit:

```text
2ab3eea
Migrate create path to subject bucket fanout
```

### Next Step

Build and review the focused Step 5 replacement tests before continuing the
remaining roadmap cleanup.

## 📅 Log Entry: June 11th, 2026 - Entry 1: Subject-Planner Naming Finalized

Completed the remaining post-Step-5 naming cleanup. The upstream subject node
is now `subject_planner_node(...)`, its router is
`route_after_subject_planner(...)`, and the parent graph wiring uses the same
names. The terminal runner now displays `SubjectBucketList` instead of the
removed planner output.

Future reference commit:

```text
bd5a7a2
Finalize subject-planner naming and runner output
```

The implementation roadmap is now ready to move into focused fanout, wrapper,
and parent integration testing.

## 📅 Log Entry: June 13th–14th, 2026 - Part 3 Deterministic Test Expansion

The June 11 entry left the newly migrated subject-planner, fanout, wrapper, and
parent-routing implementation ready for focused testing. Over the weekend, the
missing deterministic coverage was organized and built through Test 9 of the
new Part 3 Test MacroPlan.

The testing work began with a broad edge-case inventory and an executable
MacroPlan. Each test workflow received a focused microplan, review pass,
implementation, focused run, and full-suite regression run before advancing.

Existing tests were reviewed and aligned with the current graph and state
contracts. Coverage was extended for:

- checkpointed subject-planner replacement and no-subject later turns
- reducer behavior across several create slices and mixed create/update slices
- empty update patch lists completing as valid no-op updates

Six focused test files were added:

- `test_subject_fanout_v3.py` verifies no-subject, create, update, mixed,
  multi-message, shared-message, filtering, and message-order routing
- `test_extract_branch_v3.py` verifies named, sparse, and unnamed extraction,
  subject-specific prompts, wrapper contracts, and routed payload shape
- `test_update_parent_branch_v3.py` verifies routed one-profile updates,
  supporting-message filtering, no-op updates, and wrapper contracts
- `test_parent_subject_routing_integration_v3.py` verifies complete no-subject,
  create-only, update-only, and mixed parent runs with parallel merge-back
- `test_parent_multiturn_integration_v3.py` verifies checkpointed creation,
  later updates and corrections, unique accumulated messages, and thread
  isolation
- `test_parallel_update_repair_integration_v3.py` verifies parallel successful,
  model-repaired, and human-repaired updates, including several interrupts
  resumed one at a time by interrupt ID

The parallel repair tests confirmed that completed sibling branch work is
preserved while other branches remain interrupted, and that repaired branches
can be resumed individually without losing successful sibling updates.

Test 9 completed with:

```text
Focused parallel-repair file: 3 passed
Full suite: 95 passed
```

Tests 10 and 11 remain intentionally unstarted. Their coverage and workflow
placeholders remain in the MacroPlan for later work.

Future reference commit:

```text
1752e9cbeaa3a0bc3aa014b4072a75fcc907d41c
test(part3): expand deterministic fanout and integration coverage
```

## 📅 Log Entry: June 14th, 2026 - Entry 2: Extract-Subgraph Recovery Decision

While preparing Test 10, which was intended to define and test create-side
failure behavior, we reviewed the current extraction policy and found that it
was not suitable to preserve as a stable contract.

The current `extract_subgraph` performs one structured `UserProfile` extraction
and immediately commits the result. If extraction fails or returns unusable
output, the exception propagates and the create branch has no recovery path,
human fallback, or separate boundary between extraction and commit.

We decided to upgrade the create branch before writing Test 10:

- `extract_node(...)` will attempt extraction normally and retry once with the
  latest extraction error
- if both model attempts fail, the branch will interrupt for human repair
- the human will provide one complete valid `UserProfile`
- profile UUID generation and insertion into `existing` will happen only in a
  separate commit node after a valid candidate exists
- unexpected programming or infrastructure errors will continue to propagate
  rather than being hidden as repairable extraction failures

This decision postpones Test 10 until the new recovery policy is implemented.
The executable roadmap is recorded in:

- `SHORT_TERM_PLANS/SHORT_TERM_PLAN3v5.md`

## 📅 Log Entry: June 20th, 2026 - Recovery Refactor Completed

This entry completes the work opened by the June 14th recovery decision. Test
10 had been paused because create-side failure behavior was not safe enough to
freeze in deterministic tests. Instead of writing tests around a weak contract,
we first refactored the recovery architecture that those tests need to protect.

The create branch now follows the policy described in the June 14th entry:

- `ExtractAgentState` carries an uncommitted `candidate` and extraction
  `errors`
- `extract_node(...)` retries once after expected structured-output or
  validation failures
- unusable empty profiles are treated as extraction failures instead of valid
  creates
- `human_create_repair(...)` interrupts once with an explicit submit/decline
  envelope
- declined, malformed, missing-action, or invalid human create responses end
  the branch without creating a profile
- `commit_created_profile(...)` is now the only place where a UUID is generated
  and inserted into `existing`

While implementing that recovery policy, we also noticed that the update-side
human repair path had the same UX risk: after automated patch repair attempts
were exhausted, invalid human input could lead to repeated interrupts. The
update subgraph was therefore aligned with the create branch:

- `human_repair(...)` now interrupts once and expects either a submit action
  with corrective patch proposals or a decline action
- valid submitted update patches continue through
  `apply_patch(...) -> validate(...) -> commit(...)`
- declined, malformed, missing-action, wrong-target, empty, or invalid human
  update responses end the update branch without changing the original profile
- a new post-human update router decides whether to apply submitted patches or
  end the branch
- the automated model repair loop before human escalation remains unchanged

The recovery roadmap and Part 3 Test MacroPlan were updated so the remaining
test work starts from the new contract instead of the old one. Test 10 and the
later deterministic tests should now be resumed by extending the affected test
files around the new submit/decline behavior for both create and update
branches.

Future reference commit:

```text
a2ff811c9ef3885ad69ebee503dbed48e22e21ef
refactor(graph): add one-shot human recovery for create and update branches
```
