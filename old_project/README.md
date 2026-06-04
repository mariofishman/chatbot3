# Old Project

This folder contains an older, simpler chatbot experiment that predates the
current `graphv3.py` architecture.

## What It Was About

This project explored a small multi-agent pattern:

- a main agent receives the user task
- it chooses between specialized subagents
- each subagent runs with its own prompt and tool set

The goal was to learn how to:

- build a small LangGraph agent loop
- bind tools to specialized subagents
- let a higher-level agent delegate work
- render the graph as a Mermaid diagram

## What These Files Do

- `graph.py`
  Defines the old top-level delegation graph. It creates:
  - a math subagent
  - a search subagent
  - a `select_subagent` tool that lets the main agent choose one

- `my_create_agent.py`
  Contains the reusable helper that builds a simple tool-calling LangGraph
  agent from:
  - a model
  - a list of tools
  - an optional system prompt

- `tools.py`
  Defines the small tool set used by the old project:
  - arithmetic tools
  - a mocked `web_search` tool

- `utilities.py`
  Contains a tiny helper to render and save the graph diagram.

## Why It Was Moved

The current project now centers on:

- `src/graphv3.py`
- `src/state.py`

Those files implement a very different architecture focused on:

- planner-driven create and update branches
- subgraphs
- per-user update fan-out
- structured extraction and JSON patching

This `old_project/` folder is kept only as historical reference.
