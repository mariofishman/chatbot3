# Stateful Profile Construction from Conversation

## Project goal

Build a system that learns a professional profile incrementally from natural conversation, without assuming a fixed schema in advance.

In simple terms:
The system talks to a user, listens for useful information (job, company, experience, etc.), and gradually builds a structured profile over time. It does this safely and consistently, without rewriting everything or losing past information.

---

## Core idea

This is not a chatbot that outputs JSON.

This is a system that:

- detects relevant facts from conversation
- standardizes them into a shared structure
- updates a persistent profile incrementally
- maintains consistency across many users

---

## High-level architecture

## Implementation detail: subgraph

The system has three layers:

### 1. Main agent (lightweight)

- Reads conversation
- extract candidate facts
- calls the tool when relevant facts are detected
- updates state to keep any relevan future file system, to do lists, messages list, etc

---

### 2. Authoritative tool (core system)

`update_profile_safe(...)`

This tool can be implemented as an internal pipeline or as a LangGraph subgraph or agent.

This is the most important component.

Responsibilities:

- validate candidate fact structure and relevance
- detect if information is relevant
- check existing profile
- canonicalize keys (standardize naming)
- validate against registry
- apply deterministic merge
- record provenance

Simple explanation:
This tool does all the real work. It ensures the system stays correct.

---

### 3. Internal pipeline (inside the tool)

The tool may use multiple internal LLM calls:

- validate candidate structure
- normalize values
- key matching (optional)
- apply merge policies

Optional LLM usage:

- Key disambiguation (if needed)

All outputs pass through deterministic logic before any update.

Simple explanation:
The system can “think” in multiple steps internally, but only safe, validated results are saved.

---

## Core principles

### 1. The model proposes, the system decides

- LLM suggests candidate facts
- Tool validates and merges

Never the opposite.

---

### 2. Single write boundary

No other tool, node, or subgraph is allowed to mutate profile or registry.
Only one function is allowed to modify the profile and registry.

`update_profile_safe`

This prevents:

- schema drift
- inconsistent updates
- conflicting logic

## To avoid confusion, the word or concept 'state' will be used exclusively for the State the belongs to the langgraph `graph`; while the registry is a class that holds the state of the profile data it is not to be confused with the graph's State and will be simply called Registry, never Registry State.

### 3. Canonicalization

Different words → one standard key

Example:

- employer, firm, company → company

This is enforced in the tool through deterministic logic, optionally assisted by an LLM for disambiguation.

### 4. Incremental updates (no regeneration)

The profile is never rebuilt from scratch.

Instead:

- Only validated updates are applied.
- small patches/deltas are applied (using TrustCall or similar)
- existing data is preserved

---

### 5. Deterministic merge

All updates follow strict rules:

- no silent overwrites
- conflict handling is explicit
- human-in-the-loop can be triggered via interrupt when needed
- validation is primarily deterministic, with optional LLM assistance for ambiguity

---

### 6. Single authoritative write path

Even if the system uses subgraphs or sub-agents internally, all state mutation must go through one controlled entry point.

## Implementation detail: subgraph

The `update_profile_safe` tool may internally be implemented as a LangGraph subgraph.

This means:

- each internal step (validation, canonicalization, merge, etc.) can be a node
- the subgraph is invoked as a single tool by the main agent

Important constraint:
Even if implemented as a subgraph, it must behave as a single authoritative write boundary.

Only this subgraph/tool is allowed to modify:

- profile
- key registry

Simple explanation:
You can break the logic into smaller steps for clarity and debugging, but externally it must behave like one controlled operation.

## State structure

The system maintains a fixed state envelope that will be defined as the project moves forward and this state is discovered:

It could have the following fixed fields but these are only an example.

- `profile` → user-specific values
- `key_registry` → canonical schema
- `provenance` → source of each fact
- `pending_candidates` → unresolved data
- `latest_user_turn` → current input

Simple explanation:
The structure stays the same. Only the contents evolve.

---

## Registry vs profile

Important distinction:

- Registry = structure (what fields exist)
- Profile = values (what we know about this user)
- State = Graph's state that is used for the main agent or the sub-agents. Though these states could be the same they don't have to.

Example:

- registry defines: `company`
- profile stores: `"Stripe"`
- state stores: `messages`, `files`, `to_do` lists.

---

## Tool pipeline (authoritative logic)

Inside `update_profile_safe`:

1. receive candidate facts
2. validate relevance
3. check existing profile
4. canonicalize keys
5. validate against registry
6. apply deterministic merge rules (optionally using TrustCall for patch generation)
7. record provenance

The tool can return:

- update applied
- no-op (nothing to update)
- conflict detected. Human in the loop triggered.

---

## Internal LLM usage

LLMs are used for:

- extracting candidate facts (agent)
- assisting with ambiguity resolution inside the tool

LLMs are NOT used for:

- modifying canonical state directly
- defining schema permanently

---

## Runtime and tooling

- Python modules for all logic
- LangGraph for orchestration
- LangGraph Studio for execution and debugging
- LangSmith for tracing

Run with:
`langgraph dev`

Use Studio to:

- interact with the system
- inspect state transitions
- debug node behavior

---

## Suggested Project structure (adjust to improve teaching progress)

```text
profile-memory/
  AGENTS.md
  README.md
  notes.md
  langgraph.json
  .env
  src/
    state.py
    registry.py
    extraction.py
    merge.py
    provenance.py
    tool.py
    graph.py
  tests/
  examples/
```

## Suggested Development strategy (adjust to improve teaching progress)

Build in this order:

1. minimal graph skeleton
2. minimal state envelope needed by that graph
3. authoritative tool boundary
4. registry logic
5. deterministic merge logic
6. extraction
7. expand state/tool internals

Simple explanation:
Build the “safe core” first. Add AI later.

## Testing strategy

Focus on deterministic components:

- registry behavior
- canonicalization
- merge rules
- conflict handling

LLM outputs must always be:

- validated
- rejectable
- non-authoritative

## Success criteria

The system should:

- improve profile quality over time
- avoid losing information
- maintain consistent schema across users
- remain debuggable and reproducible
