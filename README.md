# Profile Memory Chatbot

## Project goal

Build a conversational system that gradually learns structured professional
information without allowing model output to write canonical profile data
directly.

The system should preserve useful facts across conversations, update profiles
incrementally, and remain deterministic and inspectable where memory correctness
matters.

## Architectural invariants

1. The graph keeps a stable outer state shape while profile contents evolve.
2. Models may propose subjects, facts, and patches, but deterministic code decides
   what can be committed.
3. Canonical profile changes follow one controlled write policy. The current
   implementation realizes that policy through validated create and update commit
   nodes; the planner and extraction steps do not write directly to the parent
   profile collection.
4. Profile updates are incremental. Existing profiles are not regenerated as an
   unrestricted model response.
5. Important validation, patch application, conflict handling, and merge behavior
   stay outside the main planning model.
6. Changes to these invariants require discussion and a corresponding README
   update.

## Current architecture

The parent graph first groups repeated mentions of each person in the incoming
message batch. Each subject is classified as either an existing profile or a new
person.

The graph then fans out one isolated branch per subject:

- The create branch extracts and validates one new profile, allows bounded repair,
  and assigns an identifier only at its commit node.
- The update branch proposes patches for one existing profile, applies and
  validates them, allows bounded repair, and commits only a validated replacement.

Each branch returns only its committed profile slice. The parent state combines
those slices by profile identifier through a deterministic reducer.

## Current scope

The profile schema is currently fixed in code. Dynamic registry growth,
cross-user schema evolution, richer provenance, and ambiguity workflows remain
future design work rather than implemented behavior.

## Documentation

- `GUIDELINES.md` contains broader design principles and open questions.
- `ARCHITECTURAL_NOTE.md` records the reasoning behind the subject-planner
  refactor.
- `LOGBOOK.md` records implementation history and current progress.
- `archive/early-design/` contains historical proposals and is not current
  architecture authority.
