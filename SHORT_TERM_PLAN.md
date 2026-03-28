# Short Term Plan

## Purpose

This file captures the current short-term implementation plan for `src/graph.py`.

It is a working plan for the next development stage and can change if implementation reveals a better approach.

## Planned Steps

1. ✅ Create a `Subagent` class with the fields `name`, `description`, `tools`, and `system_prompt`.
2. ✅ Reuse the existing toy math tools as the initial tool set for the subagent work.
3. ✅ Add a new `subtract()` `@tool` to that tool set.
4. ✅ Build a utility function that creates ReAct agents from a `Subagent`.
5. ✅ Create the first test subagent and build a dictionary of subagents in the form `{name: compiled_agent}` using that utility.
6. ✅ Create a string that lists all available subagents and what they are for.
7. Create a main-agent `@tool` that can call a subagent by name and pass it task-specific input.
8. Use the utility function to create the main agent.

## Current Notes

- The subagent will initially receive only task-specific input for its invocation.
- The subagent wrapper is intentionally simple at first.
- Command-based state updates may be added later if the tool needs to modify broader graph state.
