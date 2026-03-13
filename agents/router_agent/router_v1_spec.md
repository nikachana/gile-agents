## Router Agent v1 Specification

### 1. Purpose

Router Agent v1 performs a **first‑pass interpretation** of incoming requests and selects the **next workflow step**. Its role is to classify the request, decide where it should go next, and prepare a concise handoff for downstream components.

### 2. Scope

Router Agent v1 **does**:

- **Classify task type** – determine what kind of task the request represents.
- **Choose next route** – select the downstream agent or workflow.
- **Prepare a handoff payload** – bundle message, metadata, and context for the next step.
- **Return confidence and a short routing summary** – explain the decision at a high level.

Router Agent v1 **does not**:

- Draft final responses.
- Perform document or conversation planning.
- Perform any Georgian language refinement, translation, or validation.
- Replicate or partially re‑implement **GILE** behavior in any way.

All institutional Georgian language work remains the responsibility of the external **GILE** engine.

### 3. Routing Philosophy

- **Direct language tasks** (pure translation, rewrite, validation of text) should route straight to **GILE‑centric workflows**.
- **Reasoning, planning, and drafting tasks** should route to the **planner/reply workflows** inside `gile-agents`.
- Regardless of the path, **any final Georgian institutional output must still pass through GILE** before it is exposed outside the system.

Router v1 focuses only on **what should happen next**, not on **how language is produced or refined**.

### 4. Supported Task Types

Router Agent v1 recognizes the following task types:

- **`translate`** – convert content into institutional Georgian using GILE.
- **`rewrite`** – improve, adapt, or rephrase existing Georgian text using GILE.
- **`validate`** – check, critique, or confirm institutional Georgian text via GILE.
- **`reply_draft`** – create a draft reply message via planning/drafting workflows, then GILE.
- **`document_draft`** – produce a multi‑section draft document via planning/drafting workflows, then GILE.
- **`document_plan`** – design structure, sections, and outline only, without full drafting.
- **`needs_clarification`** – request more information from the user when the task is ambiguous.

These definitions are intentionally practical and high‑level; they describe **what** is requested, not the implementation details.

### 5. Routing Map

Router v1 maps each supported task type to a downstream target:

- **`translate`** → `gile.translate`
- **`rewrite`** → `gile.rewrite`
- **`validate`** → `gile.validate`
- **`reply_draft`** → `document_planner`
- **`document_draft`** → `document_planner`
- **`document_plan`** → `document_planner`
- **`needs_clarification`** → `clarification_flow`

The `document_planner` and `clarification_flow` are reasoning/drafting workflows in `gile-agents`, while `gile.translate`, `gile.rewrite`, and `gile.validate` are GILE‑centric paths.

### 6. Input Contract (v1)

The v1 input to Router Agent is a simple JSON object. It is intentionally minimal:

```json
{
  "message_text": "string, required – the raw user or system request",
  "metadata": {
    "channel": "optional string",
    "locale": "optional string",
    "role": "optional string (e.g., user, staff)",
    "tags": ["optional", "string", "array"]
  },
  "attachments": [
    {
      "type": "optional string (e.g., document, link)",
      "reference": "optional string identifier or URL",
      "description": "optional string"
    }
  ],
  "context": {
    "conversation_history": "optional structured data",
    "related_documents": "optional structured data",
    "additional": "optional free‑form context"
  }
}
```

- **Required**: `message_text`
- **Optional**: `metadata`, `attachments`, `context`

### 7. Output Contract (v1)

Router Agent v1 returns a structured JSON object:

```json
{
  "task_type": "string – one of translate|rewrite|validate|reply_draft|document_draft|document_plan|needs_clarification",
  "route_to": "string – identifier for the next workflow (e.g., gile.translate, document_planner)",
  "confidence": "string – one of high|medium|low",
  "reasoning_summary": "string – short natural‑language explanation of the routing decision",
  "handoff_payload": {
    "message_text": "original or normalized text to pass forward",
    "metadata": "subset of metadata relevant to the next step",
    "context": "subset of context relevant to the next step",
    "notes": "optional hints or flags for downstream agents"
  }
}
```

The **handoff_payload** is allowed to be a simplified or curated view of the input, but it must not introduce any new language refinement that belongs to GILE.

### 8. Routing Rules

Practical rules for v1 routing:

- If the request explicitly asks to **“translate”**, **“into Georgian”**, or similar, route to **`translate` → `gile.translate`**.
- If the request asks to **“rewrite”, “polish”, “improve wording”, “refine Georgian”**, route to **`rewrite` → `gile.rewrite`**.
- If the request asks to **“check”, “validate”, “ensure correctness/terminology”** for existing Georgian text, route to **`validate` → `gile.validate`**.
- If the request asks to **“draft”, “prepare”, or “write a reply”**, route to **`reply_draft` → `document_planner`** (then drafting, then GILE).
- If the request asks for a **full document**, report, or letter to be written, route to **`document_draft` → `document_planner`**.
- If the request focuses on **outline/plan/structure/sections** without requiring full text, route to **`document_plan` → `document_planner`**.
- If a request **combines drafting and refinement**, treat it as **drafting first**, then expect downstream workflows to call GILE for refinement.
- If the request is **too vague, conflicting, or underspecified**, route to **`needs_clarification` → `clarification_flow`** to collect more information.

These rules are intentionally simple and should remain easy to understand and extend.

### 9. Confidence and Fallback

Router v1 uses simple confidence bands:

- **`high`** – the intent and task type are clear and strongly match one of the supported patterns.
- **`medium`** – the decision is reasonable but there is some ambiguity or overlap with other task types.
- **`low`** – intent is unclear or multiple interpretations seem equally likely.

When confidence is **low**, Router v1 should strongly prefer **`needs_clarification`** so that the system can ask targeted follow‑up questions before committing to a workflow. Medium and high confidence may proceed with the selected route.

### 10. Non‑Goals

Router Agent v1 must **not**:

- Generate or finalize institutional Georgian text.
- Perform translation, rewrite, refinement, retrieval, editor passes, or validation – these belong to **GILE**.
- Execute complex multi‑step reasoning flows beyond task classification and routing.
- Replace the responsibilities of document planners or reply drafting agents.
- Encode business‑specific policies that should live in higher‑level orchestration.

It is a **routing and classification component**, not a language engine or planner.

### 11. Examples

| User request                                                                 | task_type          | route_to          | note                                                                        |
|-----------------------------------------------------------------------------|--------------------|-------------------|-----------------------------------------------------------------------------|
| "Please translate this email into institutional Georgian."                  | `translate`        | `gile.translate`  | Direct translation request.                                                 |
| "Refine this Georgian paragraph to match our institutional tone."           | `rewrite`          | `gile.rewrite`    | Explicit refinement of existing Georgian.                                   |
| "Check if this Georgian letter follows our terminology and fix issues."     | `validate`         | `gile.validate`   | Validation with possible corrections.                                       |
| "Draft a reply to this customer complaint in a polite tone."                | `reply_draft`      | `document_planner`| Needs planning and reply drafting before GILE refinement.                   |
| "Write a full policy document about remote work for staff."                 | `document_draft`   | `document_planner`| Multi‑section document drafting.                                            |
| "Outline the sections for a performance review form, no full text yet."     | `document_plan`    | `document_planner`| Structure and sections only.                                                |
| "Help me with this." (no context)                                           | `needs_clarification` | `clarification_flow` | Too vague; clarification required before choosing a workflow.          |

### 12. Status

This document is a **specification only**. Router Agent v1 is **not yet implemented** in runtime code, and no routing logic, API clients, or classes exist in this repository at this stage.

