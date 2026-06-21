# Short-Term Plan 4E: Live LLM And LangSmith Evaluations

## Purpose

After the Part 4 frontend/FastAPI shell is usable, add a live-model evaluation
workflow before starting the persistence architecture.

The goal is to observe how the real graph and real LLM behave through the new
browser/API surface, then collect enough evidence to guide the persistence and
deduplication work in Short-Term Plan 5.

## Position In The Roadmap

Run this after:

- `SHORT_TERM_PLAN4.md`: frontend and FastAPI migration

Run this before:

- `SHORT_TERM_PLAN5.md`: shared profile persistence, deduplication, ambiguity
  reduction, and retrieval/RAG exploration

## Scope

Build a separate live-model evaluation workflow using LangSmith.

Representative scenarios should include:

- single-turn create
- multi-turn create then update
- mixed new and existing subjects
- no-subject messages
- ambiguous or weakly identified subjects
- create-side human repair
- update-side human repair
- several simultaneous interrupts
- duplicate-risk conversations

## What To Inspect

Use LangSmith traces to inspect:

- subject classification
- candidate existing ID selection
- create/update fanout decisions
- branch prompts
- extraction and patch proposals
- validation errors
- interrupt payloads
- resume behavior
- final state changes
- latency and failure points

## Evaluation Style

Keep this separate from the normal deterministic pytest suite.

Use deterministic evaluators for invariants such as:

- valid profile shapes
- no uncommitted candidates in parent `existing`
- thread message-history isolation
- no duplicate profiles when the expected identity is clear
- interrupt IDs are preserved for repair

Use human review or LLM-as-judge evaluators for semantic quality, such as:

- whether subject classification was reasonable
- whether ambiguous subjects were handled acceptably
- whether extracted profile facts match the conversation
- whether the repair UX payload was understandable

## Non-Goals

- Do not replace deterministic pytest coverage.
- Do not require live evals for every normal test run.
- Do not build shared profile persistence here.
- Do not introduce Neo4j, LlamaIndex, or GraphRAG here.

## Definition Of Done

This evaluation phase is done when:

- a small curated LangSmith dataset exists
- the real graph can be run against the dataset
- traces are inspected for subject planning, fanout, repair, and state changes
- at least a minimal evaluator set records pass/fail signals
- findings are summarized before starting persistence work
