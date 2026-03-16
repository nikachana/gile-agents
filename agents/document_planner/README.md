## Document Planner

### Purpose

The Document Planner determines **institutional intent**, selects a **document format**, and defines the **structure and planning requirements** for responses and documents. It focuses on **what** should be communicated and **how it is organized**, not on final institutional language.

### Role and Responsibilities

The planner:

- **Detects institutional intent** using an internal taxonomy (e.g., communication, decision, documentation, confirmation, analysis).
- **Selects document format** based on the resolved intent and context, using the v1 formats:
  - `official_letter`
  - `order`
  - `meeting_minutes`
  - `certificate`
  - `memo`
- **Loads document structure** from the format library and resolves section meanings through the section vocabulary.
- **Prepares the plan for the Reply Agent** as a structured object (intent, document format, ordered sections, drafting instructions).
- **Does not produce final text** – it only defines structure and requirements.
- **Does not perform Georgian refinement** – all institutional Georgian style and polishing remain GILE’s responsibility.

The planner **does not**:

- Write final text or full sentences intended for external use.
- Perform Georgian institutional rewriting, refinement, or validation.
- Replicate or replace any of **GILE’s** language responsibilities.

### Inputs and Knowledge Sources

Likely inputs:

- Routed task and route metadata from the Router Agent.
- Source message content and conversation history.
- Relevant domain or knowledge context (documents, policies, previous decisions).

Planner configuration and knowledge (subsystem artifacts):

- `planner_v1_spec.md` – high‑level description of Planner v1 scope, responsibilities, and contracts.
- `FORMAT_SELECTION_FLOW.md` – describes how institutional intent and context are turned into a document format decision.
- `SIGNAL_MODEL.md` – explains how textual and contextual signals contribute to intent resolution and format selection.
- `decision_rules.md` – documents the rule logic that combines signals into final intent and format choices.
- `intent_taxonomy.json` – defines institutional intent categories and their allowed mappings.
- `format_library/` – defines institutional document formats and their structural templates.
- `section_vocabulary/` – defines reusable section identifiers and their semantics.
- `trigger_dictionary/` – lists trigger phrases that act as evidence for particular intents or documentation needs.
- `../HANDOFF_CONTRACTS.md` – describes the canonical Router → Planner and Planner → Reply handoff contracts in the overall agent pipeline.
- `../schemas/planner_output.schema.json` – JSON Schema for the Planner’s v1 structured output (intent, document_format, sections, draft_instructions, source_payload).

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

