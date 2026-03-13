## gile-agents

This repository contains **reasoning agents** that orchestrate and structure work, while delegating all institutional Georgian language work to the external **GILE** engine.

- **GILE (external)**: translation, rewrite, refinement, terminology enforcement, examples, validation for institutional Georgian.
- **gile-agents (this repo)**: routing, planning, and drafting logic that calls GILE as a language layer.

Agents in this repository:
- interpret and route incoming messages,
- plan documents and responses,
- draft content (often in English, sometimes in Georgian),
but they **never replicate GILE’s linguistic functionality**. All official Georgian output must be produced or finalized by GILE.

### Relationship to GILE

GILE lives in a separate repository and is treated as **external language infrastructure**. Agents call it via APIs or tools; they do not embed or re‑implement its behavior.

- **Agents**: reasoning, workflow orchestration, task decomposition, drafting.
- **GILE**: institutional Georgian translation, rewrite, refinement, validation.

### Current Status

This repository is currently a **documentation‑first scaffold**. No runtime agent logic has been implemented yet.

### Planned Next Steps

1. **Router Agent v1** – first‑pass interpretation and routing of incoming messages.
2. **Document Planner** – structure and planning for responses and documents.
3. **Reply Draft Agent** – initial reply drafting based on plans and context.
4. **GILE API integration** – HTTP and MCP integration with the external GILE engine.

