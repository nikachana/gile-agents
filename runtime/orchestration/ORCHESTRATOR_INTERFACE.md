# Orchestrator Interface v1

### Purpose

This document defines the **first executable interface** for the Orchestrator runtime component in the `gile-agents` v1 pipeline. It translates the architectural design in `ORCHESTRATOR_V1.md` and the contracts in `agents/HANDOFF_CONTRACTS.md` / `agents/schemas/` into a concrete, implementation‑oriented interface that Python code will later implement.

---

### Proposed callable interface

At the highest level, the Orchestrator exposes a **single callable entry point** that:

- accepts a **normalized request object** (the same shape that is forwarded to the Router), and
- returns a **structured orchestrator response object** (containing workflow metadata, artifacts, and final output).

Conceptually:

- **Input**: `orchestrator_request`
  - carries `message_text`, `metadata`, and `context`
  - is forwards-compatible with Router `handoff_payload`

- **Output**: `orchestrator_response`
  - carries `status`, `workflow`, `artifacts`, `final_output`, and optional `error`
  - is suitable for both user-facing delivery and internal debugging/evaluation

This interface is intentionally minimal and compatible with stubbed or real agent implementations. The first implementation may be **synchronous** (single-call, request/response style); future versions can introduce asynchronous or batched execution behind the same public interface.

---

### Input contract

The Orchestrator’s input contract is a **normalized request object** with three top-level fields:

- **`message_text`** (required, string)
  - The primary user request or system instruction, as free text.
  - This is what the Router will classify and what downstream agents will ultimately act on.

- **`metadata`** (required, object)
  - Non-textual attributes of the request, such as:
    - requester role (e.g., HR specialist, director),
    - channel (e.g., web_portal, email, API),
    - locale hints (e.g., `ka-GE`),
    - any other structured attributes known at the time of the call.
  - May be passed through to Router and onward via `handoff_payload.metadata`.

- **`context`** (required, object)
  - Case‑ or domain‑specific information, such as:
    - case or ticket identifiers,
    - employee or person identifiers,
    - references to prior steps or related documents.
  - May be passed through to Router and onward via `handoff_payload.context`.

The Orchestrator must validate that these three fields are present and of the expected basic types before calling the Router.

---

### Output contract

The Orchestrator returns a **structured response object** with the following top-level fields:

- **`status`** (required, string)
  - High-level outcome of the orchestration call.
  - Expected v1 values include, for example: `ok`, `error`, `clarification_required`.

- **`workflow`** (required, object)
  - Describes how the request was processed.
  - Suggested fields:
    - `task_type` – the Router’s `task_type` used to choose the path.
    - `route` – a short label for the executed workflow (e.g., `direct_gile`, `planner_reply_gile`, `planner_only`, `clarification`).
    - `steps_executed` – ordered list of step identifiers (e.g., `["router", "planner", "reply", "gile"]).

- **`artifacts`** (required, object)
  - Container for selected intermediate artifacts, which may include:
    - `router_output` – subset of the Router result (aligned with `router_output.schema.json`).
    - `planner_output` – subset of the Planner result (aligned with `planner_output.schema.json`).
    - `reply_draft` – subset of the Reply Agent result (aligned with `reply_output.schema.json`).
  - Artifacts can be partial but should respect the corresponding schemas conceptually.

- **`final_output`** (required for `status = ok`, object)
  - The user-facing result for successful workflows.
  - For `document_draft` / `reply_draft` paths, this will typically be **final prose text** (after GILE, if applicable).
  - For `document_plan` workflows, `final_output` may instead contain a **structured planning artifact** (e.g., sections and headings) rather than final prose.
  - Suggested fields:
    - `text` – final text or serialized representation of the plan returned to the caller.
    - `language` – language code of the final text, when applicable (e.g., `ka-GE`).

- **`error`** (optional, object)
  - Present when `status = error`.
  - High-level error description, with a machine-readable `code` and human-readable `message`.

This contract is designed to support both user delivery and internal evaluation without exposing raw agent prompts or internals.

---

### Runtime dependencies

The Orchestrator depends on **callable runtime interfaces** for the following components:

- **Router**
  - Callable that accepts the normalized request (or equivalent) and returns an object aligned with `router_output.schema.json`.
  - Provides `task_type`, `route_to`, `confidence`, `reasoning_summary`, and `handoff_payload`.

- **Document Planner**
  - Callable that accepts a payload derived from the Router’s `handoff_payload`.
  - Returns an object aligned with `planner_output.schema.json` (intent, document_format, sections, draft_instructions, source_payload).

- **Reply Agent**
  - Callable that accepts the Planner output (or a derived structure).
  - Returns an object aligned with `reply_output.schema.json` (draft_text, draft_language, draft_type, requires_gile, gile_action, source_plan).

- **GILE**
  - Callable that accepts content and metadata according to the appropriate reply → GILE handoff contract in `agents/HANDOFF_CONTRACTS.md`.
  - Returns refined institutional Georgian text and metadata suitable for final output.

In v1, the Orchestrator’s implementation will treat these as **dependencies behind stable interfaces**, not as inlined logic.

---

### Minimum v1 execution rules

The Orchestrator v1 must follow these minimum runtime rules:

- **Call Router first**
  - Always invoke the Router as the initial step given a valid input request.

- **Branch by `task_type`**
  - Use the Router’s `task_type` (and optionally `route_to`) to decide between:
    - direct GILE workflow,
    - Planner / Reply / GILE workflow,
    - Planner‑only workflow (document_plan),
    - clarification workflow.

- **Call Planner only when required**
  - For `document_draft`, `reply_draft`, and `document_plan`:
    - Invoke the Document Planner with the Router’s `handoff_payload`.
  - For `translate`, `rewrite`, `validate`, `needs_clarification`:
    - Do **not** call the Planner in v1.

- **Call Reply Agent only when required**
  - For `document_draft` and `reply_draft`:
    - Invoke the Reply Agent with the Planner’s output.
  - For `document_plan`:
    - Do **not** call the Reply Agent; return the Planner output (possibly after light wrapping).

- **Call GILE only when required**
  - For workflows that require final Georgian institutional output:
    - Invoke GILE according to the applicable reply → GILE contract.
  - For `document_plan` and pure clarification workflows:
    - Do **not** call GILE.

- **Fail fast on invalid outputs**
  - If any agent returns an output that is clearly incompatible with its documented schema/contract:
    - Stop the workflow.
    - Return `status = error` with an appropriate error code and any available artifacts.

These rules ensure that the Orchestrator reflects the approved v1 pipeline without introducing extra decision‑making.

---

### Stub-friendly design

The Orchestrator interface is intentionally designed to support **stubbed or mocked dependencies** in early development:

- **Router, Planner, Reply, and GILE can be stubbed**
  - Each dependency can be replaced by a simple stub that:
    - accepts the expected input shape, and
    - returns a deterministic, schema‑compatible output.

- **Interface stability over implementation details**
  - Early implementations can focus on wiring, error propagation, and artifact handling.
  - Actual LLM prompts, models, and detailed logic can be filled in later without changing the Orchestrator’s public interface.

- **Facilitates early tests**
  - The same interface can be used by `tests/` to exercise orchestration logic with synthetic agent responses before integrating real runtime components.

This approach allows implementation work to start incrementally while preserving the architecture defined under `agents/`.

---

### Error model

The Orchestrator v1 should use a **simple, explicit error model** for runtime failures. Suggested high-level error codes include:

- **`invalid_router_output`**
  - Router returned an output that is missing required fields or violates the conceptual `router_output.schema.json`.

- **`invalid_planner_output`**
  - Document Planner output does not align with `planner_output.schema.json` (e.g., missing `intent` or `sections`).

- **`invalid_reply_output`**
  - Reply Agent output does not align with `reply_output.schema.json` (e.g., missing `draft_text` or `draft_type`).

- **`gile_call_failed`**
  - GILE call failed, timed out, or returned an unusable result when a refined output was required.

- **`clarification_required`**
  - Router determined that more information is needed (`task_type = needs_clarification`), and the Orchestrator returns a structured clarification request rather than a final document.

Each error should be surfaced via the `error` block in the Orchestrator output, with:

- `code` – one of the high-level codes above.
- `message` – short human-readable description.
- optionally, `artifacts` – any intermediate artifacts that were successfully produced before the failure.

---

### Status

This document is the **final interface definition** for the first Orchestrator implementation in `runtime/orchestration/`. It is aligned with:

- `runtime/orchestration/ORCHESTRATOR_V1.md`
- `agents/HANDOFF_CONTRACTS.md`
- `agents/schemas/`

and is intended to be implemented in Python next, **without changing the existing architecture or contracts**.

