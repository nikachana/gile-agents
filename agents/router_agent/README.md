## Router Agent

### Purpose

The Router Agent performs a **first‑pass interpretation** of incoming messages and routes them to the appropriate downstream workflow or agent. It focuses on **classification and routing**, not on drafting or language refinement.

### Likely Future Inputs

- Incoming message (user text or system request).
- Associated metadata (channel, role, priority, domain, etc.).
- Optional source context (previous messages, related documents, task state).

### Likely Future Outputs

- Route decision (e.g., which agent or workflow to invoke).
- Task type or intent classification.
- Handoff payload containing the information required by the next agent.

### Boundaries and Non‑Goals

- **Not implemented yet** – this directory currently documents intent and contracts only; no runtime logic is present.
- Must **not** perform full drafting of responses.
- Must **not** perform Georgian language refinement, translation, or institutional style enforcement (these belong to GILE).
- Must **not** replace downstream planners or reply agents; its responsibility ends at routing and handoff.

