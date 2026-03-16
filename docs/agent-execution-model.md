# Agent execution model

### Purpose

This document explains, at a high level, **how agents execute work** in `gile-agents` and how model‑driven behavior is combined with structured reasoning and contracts. It complements `ARCHITECTURE.md` and the orchestrator design under `runtime/orchestration/`.

---

### Router – lightweight workflow classification

The **Router Agent** is responsible for **workflow classification only**:

- Inspects the normalized request (`message_text`, `metadata`, `context`).
- Assigns a `task_type` such as `translate`, `rewrite`, `validate`, `document_draft`, `reply_draft`, `document_plan`, or `needs_clarification`.
- Produces a structured routing decision and `handoff_payload` for downstream agents.

Execution characteristics:

- May use lightweight pattern matching, rules, or LLM prompts.
- Must **not** choose document formats, plan sections, or generate drafts.
- Its output shape is defined by `agents/HANDOFF_CONTRACTS.md` and `agents/schemas/router_output.schema.json`.

---

### Document Planner – structured reasoning and planning

The **Document Planner** is the core **structured reasoning** component:

- Detects **institutional intent** using a controlled taxonomy (e.g., `communication`, `decision`, `documentation`, `confirmation`, `analysis`).
- Selects a **document_format** (e.g., `official_letter`, `order`, `meeting_minutes`, `certificate`, `memo`).
- Plans **sections and structure** for the document.

The Planner relies on **structured knowledge artifacts**, not just prompts:

- `agents/document_planner/intent_taxonomy.json` – approved intent labels and mappings.
- `agents/document_planner/format_library/` – institutional document formats and structural templates.
- `agents/document_planner/section_vocabulary/` – reusable section identifiers and semantics.
- `agents/document_planner/trigger_dictionary/` – trigger phrases with signal classes and strengths.
- `agents/document_planner/SIGNAL_MODEL.md` and `decision_rules.md` – how signals combine into decisions.

Execution characteristics:

- May call models, but is anchored in **rules, taxonomies, and planning artifacts**.
- Must output a structured plan aligned with `agents/schemas/planner_output.schema.json`.
- Does **not** produce final prose or perform Georgian refinement.

---

### Reply Agent – first draft generation

The **Reply Agent** consumes the Planner’s structured output and produces the **first full draft**:

- Takes intent, document_format, sections, and draft_instructions from the Planner.
- Generates text that fills each section while respecting the planned structure.

Execution characteristics:

- May use LLMs or template‑driven logic to produce drafts.
- Must **preserve the structure** given by the Planner (sections and ordering).
- Must **not invent document format** or bypass the plan.
- Must **not** perform final institutional Georgian refinement; its drafts are input to GILE.

Its output shape is described by `agents/schemas/reply_output.schema.json` and the contracts in `agents/HANDOFF_CONTRACTS.md`.

---

### GILE – final institutional Georgian language processing

**GILE** (in the separate `gile` repository) is the **language layer**:

- Translates, rewrites, refines, and validates Georgian text.
- Enforces institutional terminology and style.
- May perform retrieval‑augmented or editor‑style passes for language quality.

Execution characteristics:

- Treats the draft content and structure as inputs; does **not** choose document formats or perform upstream reasoning.
- Is called according to the reply → GILE handoff contract documented in `agents/HANDOFF_CONTRACTS.md`.
- Is the **only component** trusted to produce or finalize institutional Georgian output.

---

### Orchestrator – sequencing and contract enforcement

The **Orchestrator** (defined in `runtime/orchestration/ORCHESTRATOR_V1.md` and `ORCHESTRATOR_INTERFACE.md`) is responsible for **sequencing and contract enforcement**:

- Accepts a normalized request object.
- Calls the Router first and branches on `task_type`.
- Invokes the Planner and Reply Agent only when required.
- Invokes GILE only when required for final Georgian processing.
- Assembles a structured response with `status`, `workflow`, `artifacts`, and `final_output`.

Execution characteristics:

- Coordinates calls; it **does not** perform reasoning or language work itself.
- Enforces adherence to the contracts defined in `agents/HANDOFF_CONTRACTS.md` and `agents/schemas/`.
- Provides a stable place to add observability, error handling, and testing around the pipeline.

---

### Not every component is “just an LLM”

In `gile-agents`:

- Some components may be implemented with LLMs, others with rules, taxonomies, or simple code.
- The **architecture‑first contracts** (in `agents/`) are the source of truth:
  - They define responsibilities, handoff shapes, and boundaries.
  - Implementations (LLM‑based or otherwise) must conform to these contracts.

The Planner in particular is designed around **structured knowledge artifacts** (taxonomies, formats, sections, signals), not only around prompt text. This makes its behavior:

- more interpretable,
- easier to test and evolve, and
- aligned with institutional expectations.

---

### See also

- `agents/router_agent/` – Router responsibilities and documentation.
- `agents/document_planner/` – Planner artifacts, signal model, and contracts.
- `agents/reply_agent/` – Reply Agent purpose and boundaries.
- `runtime/orchestration/ORCHESTRATOR_V1.md` – orchestrator runtime design.
- `runtime/orchestration/ORCHESTRATOR_INTERFACE.md` – callable orchestrator interface.
- `agents/HANDOFF_CONTRACTS.md` – canonical handoff contracts between agents.

