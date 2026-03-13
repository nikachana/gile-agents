## Router Agent

### Purpose

The Router Agent performs a **first‑pass workflow classification** of incoming messages and routes them to the appropriate downstream workflow or agent. It focuses on **classification and routing only** – it does **not** choose detailed document formats, plan sections, draft text, or refine Georgian language.

### Likely Future Inputs

- Incoming message (user text or system request).
- Associated metadata (channel, role, priority, domain, etc.).
- Optional source context (previous messages, related documents, task state).

The Router may also receive **hints about desired document format** (e.g., “official letter”, “protocol”), but the **final decision and application of document formats** belongs to the **Document Planner**, not the Router.

### Likely Future Outputs

- Route decision (e.g., which agent or workflow to invoke).
- Task type or intent classification.
- Handoff payload containing the information required by the next agent.

## Router Agent v1 Scope

Router Agent v1 is intentionally narrow in scope. It focuses on:

- **First‑pass task classification** – identify what kind of request this is.
- **Workflow routing** – decide which downstream agent or workflow should handle it.
- **Handoff preparation** – assemble the minimal payload needed by the next step.

It **does not** perform drafting, detailed document format selection, document planning, or any Georgian language refinement; these responsibilities belong to downstream agents (Document Planner, Reply Agent) and to GILE.

## Supported Task Types

Router Agent v1 is expected to classify requests into a small set of practical task types:

- **translate** – convert content into institutional Georgian via GILE.
- **rewrite** – improve or adapt existing Georgian text using GILE.
- **validate** – check or confirm institutional Georgian output via GILE.
- **reply_draft** – create a reply draft via the reply/drafting workflow (then GILE).
- **document_draft** – produce a multi‑section draft document via planning + drafting (then GILE).
- **document_plan** – prepare only the document structure and sections, without drafting final text.
- **needs_clarification** – request more information from the user before routing further.

This list is descriptive rather than exhaustive; future versions may extend it while keeping the same separation between reasoning agents and GILE.

## Routing Principle

Routing should follow a simple principle:

- **Direct language tasks** (`translate`, `rewrite`, `validate`) route toward **GILE‑centric workflows**, where GILE is the primary language engine.
- **Reasoning and drafting tasks** (`reply_draft`, `document_draft`, `document_plan`, `needs_clarification`) route toward the **planner / reply workflows** inside `gile-agents`.
- Regardless of the route, any **final Georgian institutional output must still pass through GILE** before it is returned outside the system.

## Output Contract

Router Agent v1 is expected to return a structured routing decision with at least:

- **`task_type`** – the classified task type (e.g., `translate`, `reply_draft`).
- **`route_to`** – the target agent or workflow identifier that should handle the task.
- **`confidence`** – a numeric or qualitative indication of how confident the router is in its decision.
- **`reasoning_summary`** – a short natural‑language explanation of why this route was chosen.
- **`handoff_payload`** – the data bundle (message, metadata, context) required by the next agent or workflow.

This contract is intended as a guide for future implementation and may be refined as the system evolves, while preserving the strict separation between routing, reasoning, and GILE’s language responsibilities.

### Boundaries and Non‑Goals

- **Not implemented yet** – this directory currently documents intent and contracts only; no runtime logic is present.
- Must **not** perform full drafting of responses.
- Must **not** perform Georgian language refinement, translation, or institutional style enforcement (these belong to GILE).
- Must **not** replace downstream planners or reply agents; its responsibility ends at routing and handoff.

