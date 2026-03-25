# GUIDELINES

## Purpose

This file captures the current architectural direction for the project.

It is not a fixed specification. It is a starting point for early implementation and a working set of ideas that can change as the project becomes clearer.

The architecture described here is provisional. It can and should change as the user learns more, tests ideas, and decides what actually works.

## Core Idea

The chatbot should have a natural conversation with a user and gradually learn important professional details without forcing everything into a rigid schema too early.

Over time, the system should turn those details into a structured, reusable professional profile.

## Main Principles

1. The conversation should remain flexible and human-like.
2. The system should update a profile incrementally, not regenerate the whole object each turn.
3. The graph state envelope should stay stable even if the profile contents grow.
4. The system should separate profile values from the structure that defines canonical keys.
5. New concepts can be discovered dynamically, but accepted concepts should become standardized.
6. The system should become more consistent across users over time.
7. Deterministic merge and validation logic should protect the canonical profile from noisy model outputs.

## Current Architectural Direction

The current direction is to keep a fixed top-level state shape and allow the data inside that state to evolve over time.

Examples of stable state containers may include:

1. `profile`
2. `key_registry`
3. `active_keys`
4. `provenance`
5. `pending_candidates`

The `profile` stores current user facts.

The `key_registry` stores the canonical concepts and field definitions the system has learned should exist across users.

## Update Strategy

The system should prefer partial updates, patches, or deltas over full profile regeneration.

The intended pattern is:

1. observe the latest conversational evidence,
2. propose candidate facts or candidate new keys,
3. compare candidates against the canonical registry,
4. derive the current extraction contract from the registry,
5. extract a patch or partial delta,
6. validate and merge that update deterministically into the canonical profile,
7. store provenance and any unresolved uncertainty.

## Cross-User Standardization

This project is not only about learning one user's profile in one conversation.

It is also about gradually learning a shared professional profile structure across many users.

That means:

1. similar concepts should map to the same canonical key,
2. the system should avoid drift like `company`, `firm`, and `business_name` meaning the same thing,
3. profiles should become more comparable, searchable, and reusable over time.

## Open Questions

These questions are intentionally unresolved:

1. When should a newly discovered concept become a canonical key?
2. How should conflicting facts be handled?
3. Which fields should remain free-form and which should become typed?
4. How much provenance and confidence should be stored?
5. How should follow-up questions be triggered when important profile gaps remain?
6. Whether patch-based tools such as TrustCall should be used, and where.

## Working Rule

If future implementation details conflict with this file, treat this file as guidance to revisit, not as a rigid constraint.
