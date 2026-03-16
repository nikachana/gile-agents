# Orchestrator v1

### Purpose

The Orchestrator coordinates the **runtime execution** of the `gile-agents` v1 pipeline. It is responsible for calling the right agents in the right order, passing data between them, and assembling the final result. It **does not perform agent reasoning itself** and never replaces the Router, Document Planner, Reply Agent, or GILE.

---

### Responsibilities

The Orchestrator v1 is responsible for:

- **Accepting normalized input**
  - Receive a single normalized request object containing `message_text`, `metadata`, and `context`.

- **Invoking the Router first**
  - Call the Router Agent with the normalized input.
  - Use the Router’s `task_type`, `route_to`, and `handoff_payload` as the single source of truth for workflow selection.

- **Choosing direct GILE vs planning workflow**
  - For Router task types `translate`, `rewrite`, `validate`, route to a **direct GILE workflow**.
  - For Router task types `document_draft`, `reply_draft`, `document_plan`, route to the **Planner / Reply workflow**.
  - For `needs_clarification`, produce a clarification response without invoking downstream drafting.

- **Invoking the Document Planner when needed**
  - For planning workflows, call the Document Planner with the Router’s `handoff_payload`.
  - Use the Planner’s output (intent, document_format, sections, draft_instructions, source_payload) as the plan of record.

- **Invoking the Reply Agent when needed**
  - For `document_draft` and `reply_draft` workflows, call the Reply Agent with the Planner’s structured output.
  - Use the Reply Agent’s draft output as the input to GILE.

- **Invoking GILE for final language refinement**
  - For all workflows that require final Georgian language processing, call GILE as the **final language step according to the applicable handoff contract**.
  - Pass the Reply Agent’s or direct content into GILE according to the relevant handoff contract.

- **Returning final output and optional artifacts**
  - Return a structured response containing:
    - final user-facing output,
    - high-level workflow metadata,
    - optional intermediate artifacts (Router decision, Planner plan, Reply draft) for debugging and evaluation.

The Orchestrator’s role is **pipeline coordination only**; it never makes semantic decisions that belong to the agents.

---

### Non-goals

The Orchestrator **must not**:

- **Detect institutional intent**
  - Intent detection belongs exclusively to the Document Planner, informed by its signal model and rules.

- **Choose document format**
  - Document format selection is performed only by the Document Planner.

- **Draft text**
  - Initial drafting is the responsibility of the Reply Agent (or upstream systems in direct GILE workflows).

- **Refine Georgian language**
  - All institutional Georgian refinement, style enforcement, and validation belong to GILE.

- **Duplicate agent logic**
  - The Orchestrator must not re-implement Router, Planner, Reply, or GILE logic; it only orchestrates them.

---

### Input shape (v1)

The Orchestrator expects a **normalized input** object that can be forwarded to the Router and, via handoff, to other agents.

Example:

```json
{
  "message_text": "გთხოვთ მოამზადოთ დასაქმების დამადასტურებელი ოფიციალური წერილი ჩვენი თანამშრომლისთვის.",
  "metadata": {
    "requester_role": "HR_specialist",
    "channel": "web_portal",
    "locale_hint": "ka-GE"
  },
  "context": {
    "employee_id": "EMP-12345",
    "case_id": "CASE-2026-001"
  }
}
```

The Router enriches this input with routing metadata; downstream agents receive the Router’s `handoff_payload` as their primary input.

---

### Execution flow (high-level)

At a high level, Orchestrator v1 follows this flow:

1. **Incoming request**
   - Receive normalized input (`message_text`, `metadata`, `context`).

2. **Router**
   - Call the Router Agent.
   - Read `task_type`, `route_to`, `confidence`, `reasoning_summary`, and `handoff_payload`.

3. **Branch: direct GILE path vs planning path**
   - If `task_type` ∈ {`translate`, `rewrite`, `validate`} → **direct GILE path**.
   - If `task_type` ∈ {`document_draft`, `reply_draft`, `document_plan`} → **planning path**.
   - If `task_type` = `needs_clarification` → **clarification path**.

4. **Planning path**
   - Call the Document Planner with Router’s `handoff_payload`.
   - Optionally, for `document_plan`, return the plan directly.
   - For `document_draft` and `reply_draft`, pass the Planner output to the Reply Agent.

5. **Reply path**
   - Call the Reply Agent with the Planner’s structured output.
   - Receive a draft suitable for GILE refinement.

6. **GILE**
   - For all workflows requiring Georgian institutional output, call GILE with the appropriate draft and metadata.

7. **Final output**
   - Assemble final output and selected artifacts into a structured orchestrator response.

This flow preserves the architectural separation while providing a single, coherent runtime coordination layer.

---

### Routing rules (v1)

The Orchestrator v1 interprets Router `task_type` as follows:

- **`translate` / `rewrite` / `validate` → direct GILE**
  - Route to a GILE‑centric workflow.
  - Use Router `handoff_payload` as the input content and metadata for GILE.

- **`document_draft` / `reply_draft` / `document_plan` → Planner**
  - Call the Document Planner to resolve:
    - institutional intent,
    - document_format,
    - sections and structure,
    - draft_instructions and constraints.

  - **`document_plan`**
    - May return **Planner output directly** as the final artifact if only a plan is required.

  - **`document_draft` / `reply_draft`**
    - Call the Reply Agent with the Planner output.
    - Then send the Reply Agent’s draft to GILE for final refinement.

- **`needs_clarification` → clarification response**
  - The Orchestrator constructs a clarification response (e.g., asking for missing information) based primarily on the Router decision.
  - No Planner, Reply Agent, or GILE calls are required for this path.

The Orchestrator does **not** change the meaning of `task_type`; it simply maps each task type to a fixed, documented workflow.

---

### Output shape (v1)

The Orchestrator returns a structured object that captures the workflow outcome and selected artifacts.

Example:

```json
{
  "status": "ok",
  "workflow": {
    "task_type": "document_draft",
    "route": "planner_reply_gile",
    "steps_executed": ["router", "planner", "reply", "gile"]
  },
  "artifacts": {
    "router_output": {
      "task_type": "document_draft",
      "confidence": 0.92
    },
    "planner_output": {
      "intent": "communication",
      "document_format": "official_letter"
    },
    "reply_draft": {
      "draft_text": "We hereby confirm that ...",
      "draft_language": "ka-GE"
    }
  },
  "final_output": {
    "text": "ამით ვადასტურებთ, რომ ...",
    "language": "ka-GE"
  }
}
```

The exact fidelity of embedded artifacts may be configurable, but the Orchestrator should be able to expose enough detail to support debugging and evaluation.

---

### Error handling principles (v1)

Orchestrator v1 follows simple, conservative error-handling rules:

- **Fail fast on invalid agent outputs**
  - If any agent returns an output that does not satisfy its documented contract (see `agents/HANDOFF_CONTRACTS.md` and `agents/schemas/`), the Orchestrator should treat this as a hard error for v1.

- **Preserve intermediate artifacts where possible**
  - When failing, include any successfully produced artifacts (e.g., Router or Planner output) in an error response for debugging and analysis.

- **Do not silently skip required steps**
  - The Orchestrator must not “recover” by skipping Planner, Reply, or GILE when they are required for a given workflow.
  - Any deviation from the documented flow should surface as an explicit error, not as a hidden fallback.

In v1, resilience is secondary to **contract clarity and observability**.

---

### Relationship to existing artifacts

Orchestrator v1 is defined in relation to the existing architectural documentation and schemas:

- `agents/HANDOFF_CONTRACTS.md`
  - Defines the canonical handoff contracts between Router, Document Planner, Reply Agent, and GILE.
  - The Orchestrator must respect these contracts and never change their semantics at runtime.

- `agents/schemas/`
  - Provides documentation-level JSON Schemas for Router, Planner, and Reply outputs.
  - The Orchestrator should treat these schemas as the expected shapes for validating agent interactions.

- `runtime/README.md`
  - Describes the separation between architectural specifications (`agents/`) and executable runtime code (`runtime/`).
  - Orchestrator v1 lives in `runtime/orchestration/` as part of the runtime design layer, not as implementation code.

The Orchestrator **binds these artifacts together at runtime** without changing their design.

---

### Status

This document defines the **v1 runtime design** for the Orchestrator in the `gile-agents` pipeline. It is a documentation artifact only and **is not yet executable code**. Future work may implement this design in code under `runtime/orchestration/` while preserving the existing architecture, contracts, and agent responsibilities.

