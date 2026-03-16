# Architecture overview

### What is `gile-agents`?

`gile-agents` is the **reasoning and orchestration layer** around the external `gile` institutional Georgian language engine. It defines agents, contracts, and runtime flows that:

- interpret incoming requests,
- plan documents and replies,
- generate first drafts, and
- call GILE to produce final institutional Georgian output.

`gile` remains the **language layer** (translation, rewrite, refinement, terminology, validation). `gile-agents` remains the **reasoning and workflow layer**.

---

### End‑to‑end request flow

At a high level, the pipeline works as follows:

1. **User Request**
   - A normalized request arrives with `message_text`, `metadata`, and `context`.

2. **Router Agent (workflow classification)**
   - Classifies the request into a workflow task type (e.g., `translate`, `document_draft`, `reply_draft`, `document_plan`, `needs_clarification`).

3. **Document Planner (intent + format + sections)**
   - For planning workflows, detects institutional intent, selects a document format, and plans sections and structure.

4. **Reply Agent (first draft)**
   - For drafting workflows, converts the plan into a first full draft, aligned with the planned structure.

5. **GILE (language layer)**
   - Performs final Georgian language processing: translation, rewrite, refinement, terminology enforcement, and validation.

6. **Institutional Georgian Output**
   - Final output, suitable for institutional use, is returned to the caller.

An Orchestrator in `runtime/` coordinates these steps but does **not** replace any agent’s responsibilities.

---

### Repository layout

The main directories are:

- **`agents/`**
  - Architectural specifications and contracts for the agent layer.
  - Includes Router, Document Planner, Reply Agent, handoff contracts, schemas, and planner signal models.

- **`runtime/`**
  - Will contain **executable runtime implementations** (e.g., orchestrator, adapters).
  - Executes the architecture defined under `agents/` but does not redefine it.

- **`prompts/`**
  - Will contain **LLM prompt templates and prompt-building logic** used by runtime components and agents.

- **`tests/`**
  - Will contain **evaluation, regression, and workflow tests** for the runtime behavior and contracts.

- **`docs/`**
  - High‑level documentation for contributors (including this file) and integration guides.

---

### How `gile-agents` relates to `gile`

- `gile` (separate repository):
  - Implements the **language engine** for institutional Georgian.
  - Handles translation, rewrite, refinement, terminology, and validation.

- `gile-agents` (this repository):
  - Implements the **reasoning, planning, and orchestration** around GILE.
  - Ensures that every final institutional Georgian output passes through GILE.

`gile-agents` never re‑implements GILE’s language responsibilities; instead, it focuses on **deciding what needs to be said and how it should be structured** before GILE finalizes the language.

---

### Key contracts and orchestration

Two key documentation pillars define how agents interact:

- `agents/HANDOFF_CONTRACTS.md`
  - Canonical JSON‑shaped contracts between Router, Document Planner, Reply Agent, and GILE.

- `agents/schemas/`
  - Documentation‑level JSON Schemas that mirror those contracts.

The Orchestrator design in `runtime/orchestration/` (see `ORCHESTRATOR_V1.md` and `ORCHESTRATOR_INTERFACE.md`) describes how these contracts are executed at runtime.

---

### See also

- `ARCHITECTURE.md` – high‑level two‑repository architecture and language vs reasoning separation.
- `agents/HANDOFF_CONTRACTS.md` – detailed agent handoff contracts.
- `runtime/orchestration/ORCHESTRATOR_V1.md` – orchestrator runtime design.
- `docs/agent-execution-model.md` – execution model across Router, Planner, Reply Agent, GILE, and Orchestrator.

