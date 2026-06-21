# Short-Term Plan 4: Frontend And FastAPI Migration From Chatbot2

## Purpose

Start Part 4 by creating a usable browser chat interface for `graphv3.py`.

This phase reuses proven frontend and FastAPI shell code from the read-only
reference project at:

```text
/Users/mariofishman/projects/chatbot2
```

The goal is not to copy chatbot2's graph logic. `src/graphv3.py` remains the
authoritative graph. Chatbot2 is only a reference for the API shell, streaming
transport, frontend reducer, chat UI, thread ID handling, interrupt handling,
and abort lifecycle.

## Compatibility With Completed Part 3

Stage 4 starts after the Part 3 graph work recorded in `LOGBOOK.md` and
`SHORT_TERM_PLAN3v5.md`. The frontend/API layer should wrap that completed
graph rather than redesign it.

Important current contracts:

- `graphv3.py` is primarily a memory-update graph. A successful turn may
  produce profile state changes without producing visible assistant text.
- `MainState.messages` requires human messages, and `subject_planner_node(...)`
  requires every human message to have a stable unique `id`.
- The backend must create `HumanMessage` objects with unique IDs before
  invoking the graph.
- The backend must invoke the compiled graph with
  `configurable.thread_id` so LangGraph checkpoint state is isolated by
  conversation thread.
- `app_user_id` is an API/frontend boundary value for Stage 5. It should be
  accepted, logged, and carried at the endpoint boundary, but it should not be
  inserted into `MainState` until the persistence architecture is added.
- Any emitted `state` event must be a compact JSON-safe snapshot, not raw
  Pydantic models or raw LangChain message objects.
- Do not stream internal LLM prompts, structured-output calls, or repair
  reasoning as user-visible assistant chat text.

## Safety Rule

Treat chatbot2 as read-only reference material.

- Do not edit, delete, move, format, stage, or commit files in chatbot2.
- Copy selected files into chatbot3 before adapting them.
- Make all edits only inside `/Users/mariofishman/projects/chatbot3`.

## What We Found In Chatbot2

### Backend Files Reviewed

- `backend/app/main.py`
- `backend/app/graph/graph.py`
- `backend/app/graph/templates.py`
- `backend/requirements.txt`

Reusable backend ideas:

- FastAPI app setup
- CORS setup for Vite dev server
- `/health` endpoint
- `/chat` endpoint
- POST-based SSE streaming with `StreamingResponse`
- backend-owned `thread_id`
- `Command(resume=...)` support
- explicit SSE event types:
  - `thread_id`
  - `text`
  - `interrupt`
  - `done`
  - `abort`
  - `error`
- multiline-safe SSE formatting idea

Backend code that should not be copied directly:

- chatbot2's `backend/app/graph/graph.py`
- chatbot2's graph nodes, prompts, schemas, and TrustCall extraction logic
- chatbot2's old assumption that a resume payload is just a plain string

Reason: chatbot3 has a much richer `graphv3.py` with subject planning,
parallel fanout, create/update subgraphs, structured repair envelopes, and
multi-interrupt behavior.

### Frontend Files Reviewed

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/streamSSE.ts`
- `frontend/src/index.css`
- `frontend/src/components/ChatArea.tsx`
- `frontend/src/components/InputArea.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/components/MessageBubble.tsx`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/src/components/ui/scroll-area.tsx`
- `frontend/src/components/ui/textarea.tsx`
- `frontend/src/lib/utils.ts`

Reusable frontend ideas:

- Vite + React + TypeScript + Tailwind structure
- shadcn-style UI primitives
- reducer-driven chat state
- incremental token rendering
- abort with `AbortController`
- Escape-key cancellation
- markdown rendering with list-marker CSS fix
- thread ID received from SSE and sent on later turns
- frontend-owned intent selection:
  - normal message when not interrupted
  - resume payload when interrupted

Frontend code that should be adapted before use:

- `App.tsx` has debugging leftovers and should be cleaned.
- `streamSSE.ts` currently treats interrupt payload too simply.
- `Layout.tsx` uses `any` props and should be typed.
- The UI currently has no display for pending interrupt details.
- The frontend currently assumes one pending interrupt, while chatbot3 can
  produce several simultaneous interrupts.

## Selected Files To Copy First

Copy these as a starting shell:

```text
chatbot2/frontend/package.json
chatbot2/frontend/package-lock.json
chatbot2/frontend/index.html
chatbot2/frontend/vite.config.ts
chatbot2/frontend/tsconfig.json
chatbot2/frontend/tsconfig.app.json
chatbot2/frontend/tsconfig.node.json
chatbot2/frontend/components.json
chatbot2/frontend/eslint.config.js
chatbot2/frontend/src/main.tsx
chatbot2/frontend/src/index.css
chatbot2/frontend/src/App.tsx
chatbot2/frontend/src/streamSSE.ts
chatbot2/frontend/src/components/
chatbot2/frontend/src/lib/
```

Copy or recreate these backend pieces in chatbot3:

```text
chatbot2/backend/app/main.py
```

Do not copy:

```text
chatbot2/backend/app/graph/
chatbot2/backend/checkpoints.sqlite
chatbot2/backend/app/graph/checkpoints.db
chatbot2/backend/.venv/
chatbot2/frontend/node_modules/
```

## Target Chatbot3 Structure

Prefer this structure unless a better repo-local convention appears during
implementation:

```text
backend/
  app/
    __init__.py
    main.py

frontend/
  package.json
  ...
  src/
    App.tsx
    streamSSE.ts
    components/
    lib/
```

The backend should import the graph from chatbot3's current source, not from
chatbot2:

```python
from src.graphv3 import graph
```

If import-path problems appear, solve them locally in chatbot3 rather than
changing chatbot2.

## Backend Adaptation Requirements

The FastAPI endpoint must adapt to chatbot3's graph contract.

### Request Shape

Support:

- `message`: a new user message
- `resume`: a mapping of LangGraph interrupt IDs to human repair payloads
- `thread_id`: optional on first request, required for resume
- `app_user_id`: a temporary dev/manual user identity used only to prepare the
  API/frontend boundary for later app-user-scoped profile persistence

`message` and `resume` must be mutually exclusive.

Real authentication is out of scope for this phase. For now, `app_user_id` may
come from a simple frontend selector, local browser storage, or a development
default. The important requirement is that the request/endpoint shape already
has a place for user identity before the persistence layer needs it.

This does not mean profiles are globally shared or owned directly by one
authenticated account. It only establishes the temporary app-user scope that
Plan 5 will use when saving app-user-scoped `UserProfile` records. A later
identity-linking layer may connect separate users' profile records when they
appear to describe the same real-world person.

The resume payload must support chatbot3's explicit repair envelopes, such as:

```json
{
  "action": "submit",
  "profile": {
    "name": "Lucia",
    "role": "Lawyer"
  }
}
```

and:

```json
{
  "action": "decline"
}
```

For update repair:

```json
{
  "action": "submit",
  "patches": {
    "items": []
  }
}
```

### SSE Event Shape

Keep or add these event types:

- `thread_id`: emitted once near stream start
- `text`: optional visible assistant text, if graph streaming exposes it
- `state`: optional compact state snapshot for development inspection
- `interrupt`: pending interrupt payloads, including interrupt IDs
- `done`: normal completion
- `abort`: user/client cancellation
- `error`: backend or graph failure

Each stream should have exactly one terminal event:

- `done` for normal completion
- `interrupt` when the graph pauses for human repair
- `abort` when the client cancels
- `error` when the backend or graph fails

Do not emit `done` after an `interrupt`, `abort`, or `error`.

Important: chatbot3 may produce several simultaneous interrupts. The backend
must preserve interrupt IDs so the frontend can resume one interrupt at a time
or submit several repairs when appropriate.

### Backend Non-Goals For This Phase

- Do not build app-user-scoped profile persistence here.
- Do not add Neo4j, LlamaIndex, or GraphRAG yet.
- Do not rewrite `graphv3.py` unless the endpoint reveals a small integration
  bug.
- Do not make the frontend depend on persistence behavior that does not exist
  yet.

## Frontend Adaptation Requirements

The frontend must support the current graph's human repair UX.

### State Model

Start from chatbot2's reducer, then extend it to track:

- messages
- streaming
- thread ID
- temporary app user ID
- a local list of known conversation threads
- the active conversation thread
- pending interrupts
- last state snapshot, if the backend emits one
- error state

### Thread And Session UX

This frontend phase should support browser-level thread management even before
app-user-scoped profile persistence exists.

Minimum viable thread UX:

- start a new conversation with no `thread_id`
- receive and store the backend-assigned `thread_id`
- continue sending later turns with the active `thread_id`
- keep a local list of recent thread IDs created in this browser session
- switch between locally known threads for manual testing
- make clear that each thread has isolated LangGraph message/checkpoint state

Minimum viable app-user identity UX:

- expose a simple development user selector or editable `app_user_id`
- persist the selected `app_user_id` locally in the browser
- send `app_user_id` with every `/chat` request
- keep locally known thread IDs grouped by `app_user_id`, or clear the active
  thread when the development user changes
- make clear that this is not authentication yet
- preserve the boundary so Plan 5 can route persistence reads/writes to the
  correct app-user-scoped profile records
- avoid implying that one user's `UserProfile` updates will overwrite another
  user's profile record for a similar real-world person

Out of scope for this phase:

- app-user-scoped profile persistence across different thread IDs
- durable session history after browser storage is cleared
- database-backed session listing
- multi-user account/session management
- secure authentication or authorization

### Interrupt UX

Minimum viable UX:

- show pending interrupt payloads
- show the interrupt ID for debugging
- allow the user to submit a JSON response for a selected interrupt
- allow decline responses
- resume with the same `thread_id`
- support resolving one pending interrupt at a time by sending a resume map
  keyed by the selected LangGraph interrupt ID
- keep unresolved interrupts visible after a partial resume response

The first version may use a developer-style JSON textarea. A polished repair
form can come later.

### Streaming UX

Keep:

- incremental assistant text rendering when a future graph/API response exposes
  visible assistant text
- Stop button
- Escape-to-abort
- Markdown rendering
- thread continuity across turns

Adapt:

- normal completion display so memory-only turns can finish without assistant
  text
- interrupt handling from one pending interrupt to a list/map of interrupts
- resume request body from plain text to interrupt-ID keyed payloads
- error and abort display so the user understands why a stream ended

## Execution Roadmap

Complete one step at a time.

### Step 1: Create Backend Shell

Copy or recreate the FastAPI shell from chatbot2 into chatbot3.

Deliverables:

- [ ] `backend/app/main.py`
- [ ] `/health`
- [ ] `/chat`
- [ ] CORS for Vite dev server
- [ ] request model with mutually exclusive `message` and `resume`
- [ ] request model accepts a temporary `app_user_id` without using it for
  persistence yet

Stop before frontend work until `/health` runs.

### Step 2: Connect Backend To `graphv3.py`

Adapt `/chat` to call chatbot3's compiled `graph`.

Deliverables:

- [ ] new message invocation with `HumanMessage`
- [ ] backend creates a stable unique ID for each new `HumanMessage`
- [ ] resume invocation with `Command(resume=...)`
- [ ] backend-owned `thread_id`
- [ ] accepted `app_user_id` is carried through the API boundary for future
  app-user-scoped persistence work without being inserted into `MainState`
- [ ] SSE `thread_id`, `interrupt`, `done`, `abort`, and `error`
- [ ] exactly one terminal SSE event per request
- [ ] enough logging or state output for development debugging

Run a terminal/manual request before copying the frontend.

### Step 3: Copy Frontend Shell

Copy selected frontend files into `frontend/`.

Deliverables:

- [ ] Vite app starts
- [ ] imported UI components compile
- [ ] `streamSSE.ts` parses known events
- [ ] old debugging leftovers removed

### Step 4: Adapt Frontend Request/Reducer Contract

Adapt the reducer and request body to chatbot3's event contract.

Deliverables:

- [ ] normal message sends `{message, thread_id}`
- [ ] interrupt repair sends `{resume, thread_id}`
- [ ] every request also includes the current temporary `app_user_id`
- [ ] pending interrupts are stored with IDs
- [ ] received thread IDs are stored as locally known conversations
- [ ] switching the active thread changes which `thread_id` is sent next
- [ ] errors and aborts are visible enough for development

### Step 5: Add Minimal Thread Controls

Add a simple developer-facing thread control panel.

Deliverables:

- [ ] display or edit the current temporary `app_user_id`
- [ ] display the active thread ID
- [ ] create a new conversation by clearing the active thread ID before sending
- [ ] list recent local thread IDs
- [ ] switch the active thread ID
- [ ] clear or switch the active thread when the temporary `app_user_id` changes
- [ ] do not promise profile persistence across threads yet
- [ ] do not promise deduplication or identity-linking across app users yet

### Step 6: Add Minimal Interrupt Repair UI

Add a simple developer-facing interrupt panel.

Deliverables:

- [ ] list pending interrupts
- [ ] inspect payload
- [ ] paste JSON response
- [ ] submit response for one interrupt ID
- [ ] preserve the other pending interrupts when only one interrupt is resumed
- [ ] support decline action

Do not over-polish the UI yet.

### Step 7: Manual End-To-End Scenarios

Use the browser to verify:

- [ ] first message creates a thread ID
- [ ] second message reuses the thread ID
- [ ] every new backend-created human message has a unique message ID
- [ ] requests include the selected temporary `app_user_id`
- [ ] changing `app_user_id` changes the identity value sent to the backend without
  pretending authentication exists
- [ ] changing `app_user_id` does not accidentally continue a thread created under
  a different development user
- [ ] switching to a new thread creates isolated message/checkpoint state
- [ ] switching back to a previous local thread reuses that thread's checkpointed
  graph state
- [ ] memory-only graph turns can complete without visible assistant text while
  still exposing useful state or completion feedback
- [ ] create path can complete
- [ ] update path can complete
- [ ] create repair interrupt can be displayed and resumed
- [ ] update repair interrupt can be displayed and resumed
- [ ] multiple pending interrupts are visible and addressable by ID
- [ ] Stop/Escape abort still works

### Step 8: Decide What To Polish Next

After the shell works, choose between:

- [ ] improving frontend UX
- [ ] adding endpoint tests
- [ ] adding app-user-scoped profile persistence
- [ ] adding LangSmith/live-LLM evaluation flow

## Definition Of Done

Part 4 frontend/FastAPI migration is done when:

- [ ] chatbot3 has its own FastAPI backend shell
- [ ] chatbot3 has its own React frontend shell
- [ ] the frontend can send messages through the FastAPI backend to `graphv3.py`
- [ ] the frontend can show useful completion/state feedback even when `graphv3.py`
  produces no visible assistant text
- [ ] the frontend/API can carry a temporary `app_user_id` for future persistence
  routing of app-user-scoped profile records without implementing
  authentication
- [ ] backend-created human messages have stable unique IDs compatible with
  `subject_planner_node(...)`
- [ ] the frontend can keep and reuse `thread_id`
- [ ] the frontend can start and switch between locally known thread IDs for
  testing thread-scoped graph state
- [ ] thread controls do not mix local thread IDs across temporary `app_user_id`
  values
- [ ] the frontend can display pending interrupts
- [ ] the frontend can resume at least one interrupt by ID
- [ ] the frontend can leave other pending interrupts visible when only one
  interrupt is resolved
- [ ] chatbot2 remains untouched
