## Document Planner

### Purpose

The Document Planner determines **institutional intent**, selects a **document format**, and defines the **structure and planning requirements** for responses and documents. It focuses on **what** should be communicated and **how it is organized**, not on final institutional language.

### Role and Responsibilities

The planner:

- **Selects institutional intent** using an internal taxonomy (e.g., communication, decision, documentation, confirmation, analysis).
- **Maps intent to a document format** using the v1 formats:
  - `official_letter`
  - `order`
  - `meeting_minutes`
  - `certificate`
  - `memo`
- **Loads section structures** from the section vocabulary and format library.
- Produces a **structured plan** (plan type, document format, ordered sections, drafting instructions) for the Reply Agent.

The planner **does not**:

- Write final text or full sentences intended for external use.
- Perform Georgian institutional rewriting, refinement, or validation.
- Replicate or replace any of **GILE’s** language responsibilities.

### Inputs and Knowledge Sources

Likely inputs:

- Routed task and route metadata from the Router Agent.
- Source message content and conversation history.
- Relevant domain or knowledge context (documents, policies, previous decisions).

Planner configuration and knowledge:

- `intent_taxonomy.json` – defines institutional intent categories and their default formats.
- `format_library/` – defines institutional document formats and their structural templates.
- `section_vocabulary/` – defines reusable section identifiers and their semantics.

### Outputs

Planner outputs typically include:

- High‑level plan for the response or document (plan type and selected format).
- Proposed structure and sections (headings, subsections, ordering).
- Required elements and constraints (e.g., mandatory sections, disclaimers).
- Drafting instructions for downstream drafting agents.

### Boundaries and Non‑Goals

- **Not implemented yet** – this directory currently defines intent and contracts only; no runtime logic is present.
- Must **not** perform final Georgian institutional writing.
- Must **not** duplicate GILE’s translation, rewrite, refinement, or validation responsibilities.
- May outline example phrasing at a conceptual level, but final wording for institutional Georgian must be produced or finalized by GILE.

