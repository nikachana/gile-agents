## Document Planner

### Purpose

The Document Planner determines the **structure and planning requirements** for responses and documents. It focuses on **what** should be communicated and **how it is organized**, not on final institutional language.

### Likely Future Inputs

- Routed task and route metadata from the Router Agent.
- Source message content and conversation history.
- Relevant domain or knowledge context (documents, policies, previous decisions).

### Likely Future Outputs

- High‑level plan for the response or document.
- Proposed structure and sections (headings, subsections, ordering).
- Required elements and constraints (e.g., mandatory sections, disclaimers).
- Drafting instructions for downstream drafting agents.

## Document Formats

The Document Planner is expected to recognize **institutional document formats** and use them to generate structured plans.
Examples include:

- `official_letter`
- `meeting_minutes`
- `protocol`
- `memo`
- `decree`
- `certificate`

These formats act as **structural templates** (sections, ordering, required elements). The planner selects and applies them when building plans, while **GILE** remains responsible only for **language‑level refinement** of the drafted content.

### Boundaries and Non‑Goals

- **Not implemented yet** – this directory currently defines intent and contracts only; no runtime logic is present.
- Must **not** perform final Georgian institutional writing.
- Must **not** duplicate GILE’s translation, rewrite, refinement, or validation responsibilities.
- May outline example phrasing at a conceptual level, but final wording for institutional Georgian must be produced or finalized by GILE.

