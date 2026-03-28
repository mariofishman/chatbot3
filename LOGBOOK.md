# Project Logbook - Professional Profile Chatbot

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
