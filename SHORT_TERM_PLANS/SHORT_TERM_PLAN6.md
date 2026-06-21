# Short-Term Plan 6: Controlled Memory Schema Evolution

## Purpose

After the Stage 5 graph memory layer works reliably with a manually governed
schema, add a controlled way for the system to notice when conversations may
require new entity types, relationship types, or properties.

This is not part of Stage 5. Stage 5 should persist memory using the initial
manual schema only.

## Problem

A fixed memory schema is safer for the first graph persistence layer, but over
time conversations may reveal useful concepts that do not fit the original
schema.

Examples:

- a recurring kind of entity not represented by the initial node labels
- a relationship that appears often but has no approved relationship type
- a property that would improve retrieval or disambiguation

The system should eventually help discover these gaps without giving the LLM
permission to mutate the database schema directly.

## Scope

Build a controlled ontology/schema evolution workflow.

The system may:

- detect candidate new node labels
- detect candidate new relationship types
- detect candidate new properties
- explain why the existing schema is insufficient
- propose a schema change for human review
- collect examples from conversation traces

The system must not:

- automatically alter the Neo4j schema
- allow arbitrary labels, relationships, or properties in production writes
- bypass the custom writer layer from Stage 5

## Required Safety Boundary

Schema evolution should be proposal-only.

Flow:

```text
conversation evidence
  -> schema gap detector
  -> proposed schema change
  -> human review
  -> manually approved schema migration
  -> writer/schema update
```

Only approved schema changes should become valid primitives for the Stage 5
writer layer.

## Definition Of Done

This phase is done when:

- schema gaps can be detected and summarized
- proposed node, relationship, or property additions are represented
  structurally
- proposals include supporting examples
- no proposal can directly mutate Neo4j
- approved schema changes can be manually incorporated into the writer/schema
  registry
