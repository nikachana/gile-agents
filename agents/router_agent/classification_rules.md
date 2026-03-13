## Router Agent Classification Rules (v1)

This document describes how the **Router Agent** classifies incoming requests into **workflow‑level task types**. It is a design document only; no runtime routing logic exists yet.

### 1. Scope of the Router

The Router Agent:

- Performs **first‑pass workflow classification** for each incoming message.
- Decides **which downstream workflow** should handle the request (e.g., GILE vs. Document Planner).
- Prepares a **handoff payload** for the next agent.

The Router Agent **does not**:

- Choose detailed **document formats** (this belongs to the Document Planner).
- Perform **document planning** (intent, format, section structure).
- Draft text or create full responses (this belongs to the Reply Agent).
- Perform any **Georgian language refinement, translation, or validation** (this belongs to GILE).

### 2. Supported Task Types

Router v1 classifies requests into the following task types:

- `translate`
- `rewrite`
- `validate`
- `reply_draft`
- `document_draft`
- `document_plan`
- `needs_clarification`

### 3. Routing Map

Each task type is mapped to a downstream workflow:

- `translate` → `gile.translate`
- `rewrite` → `gile.rewrite`
- `validate` → `gile.validate`
- `reply_draft` → `document_planner`
- `document_draft` → `document_planner`
- `document_plan` → `document_planner`
- `needs_clarification` → `clarification_flow`

GILE‑centric routes handle **pure language operations**. Planner‑centric routes handle **reasoning and document planning**, before any call to GILE.

### 4. Practical Classification Rules

#### 4.1 Direct language tasks (GILE‑centric)

- If the request explicitly asks to **translate** content into institutional Georgian, classify as:
  - **task_type**: `translate`
  - **route_to**: `gile.translate`
- If the request asks to **rewrite, polish, improve wording, refine Georgian**, or similar, classify as:
  - **task_type**: `rewrite`
  - **route_to**: `gile.rewrite`
- If the request asks to **check, validate, or ensure correctness/terminology** for existing Georgian text, classify as:
  - **task_type**: `validate`
  - **route_to**: `gile.validate`

These cases are **direct language operations**; Router sends them straight to GILE‑centric workflows.

#### 4.2 Reply drafting tasks

- If the request asks to **draft, prepare, or write a reply** (e.g., response to a complaint, answer to an inquiry), classify as:
  - **task_type**: `reply_draft`
  - **route_to**: `document_planner`

The Document Planner will then select intent and format (if needed), and the Reply Agent will draft text; GILE will refine language afterward.

#### 4.3 Document drafting tasks

- If the request asks to **draft or write a full institutional document** (e.g., order, meeting minutes, certificate, internal memo), classify as:
  - **task_type**: `document_draft`
  - **route_to**: `document_planner`

Examples:

- “Draft an **order** about new working hours.” → `document_draft`
- “Write **meeting minutes** for today’s board meeting.” → `document_draft`
- “Prepare a **certificate** of employment.” → `document_draft`
- “Draft an internal **memo** about the new policy.” → `document_draft`

The Router **does not decide** which specific format (order, minutes, certificate, memo) to apply; it only classifies that a **document_draft** workflow is needed.

#### 4.4 Document planning (outline/structure) tasks

- If the request focuses on **outline, plan, or structure** without requiring full text, classify as:
  - **task_type**: `document_plan`
  - **route_to**: `document_planner`

Examples:

- “Outline the sections for an official letter.” → `document_plan`
- “Give me the structure for meeting minutes.” → `document_plan`
- “Plan the sections of an internal memo about remote work.” → `document_plan`

The Document Planner will choose an intent, select the appropriate format, and return a section‑level plan.

#### 4.5 Needs clarification

- If the request is **too vague, incomplete, or conflicting** to classify reliably, use:
  - **task_type**: `needs_clarification`
  - **route_to**: `clarification_flow`

Example:

- “Help me with this.” (no context) → `needs_clarification`

The clarification flow is responsible for collecting additional information before the Router or Planner proceeds.

### 5. Distinguishing Router vs. Planner Responsibilities

- **Router Agent**:
  - Classifies the **workflow type** (e.g., `translate` vs. `document_draft`).
  - Sends requests either to **GILE‑centric** routes or to the **Document Planner**.
- **Document Planner**:
  - Selects **institutional intent** (communication, decision, documentation, confirmation, analysis).
  - Selects the **document format** (v1: `official_letter`, `order`, `meeting_minutes`, `certificate`, `memo`).
  - Loads and configures **section structures** for the chosen format.

The Router never chooses detailed document formats; it only decides **which type of workflow** should run next.

### 6. Compact Examples: Router Output vs. Planner Responsibilities

#### Example A – Citizen complaint reply

- User request: “Please draft a reply to this citizen complaint about delayed service.”
- **Router output** (simplified):
  - `task_type`: `reply_draft`
  - `route_to`: `document_planner`
  - `confidence`: `high`
- **Planner responsibilities**:
  - Interpret intent as **communication**.
  - Decide whether a simple **reply structure** is sufficient (no special document format), or map to a format if needed.
  - Produce sections (e.g., greeting, acknowledgment, explanation, closing) and instructions for the Reply Agent.

#### Example B – Meeting minutes

- User request: “Write meeting minutes for today’s coordination meeting.”
- **Router output**:
  - `task_type`: `document_draft`
  - `route_to`: `document_planner`
  - `confidence`: `high`
- **Planner responsibilities**:
  - Interpret intent as **documentation**.
  - Select format `meeting_minutes`.
  - Load sections (e.g., header, meeting_details, participants, agenda, discussion_summary, decisions, action_items).

#### Example C – Translation only

- User request: “Translate this decision into institutional Georgian.”
- **Router output**:
  - `task_type`: `translate`
  - `route_to`: `gile.translate`
  - `confidence`: `high`
- **Planner responsibilities**:
  - **None** for this request; the Router has routed directly to GILE because no new document structure or planning is required.

