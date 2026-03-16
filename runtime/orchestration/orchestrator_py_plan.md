# Python Implementation Plan for Orchestrator v1

### Purpose

This document translates the orchestrator runtime design (`ORCHESTRATOR_V1.md` and `ORCHESTRATOR_INTERFACE.md`) into a minimal **first Python implementation plan**. It describes the initial `orchestrator.py` responsibilities, dependency model, and helper structure without specifying concrete code or changing the approved architecture.

---

### Proposed file

The first executable orchestrator code will live in:

- `runtime/orchestration/orchestrator.py`

This module will implement the callable interface defined in `ORCHESTRATOR_INTERFACE.md`, using the contracts in `agents/HANDOFF_CONTRACTS.md` and `agents/schemas/` as its reference for input and output shapes.

---

### Minimum implementation scope (v1)

The v1 Python implementation should do **exactly** the following:

- **Accept normalized input**
  - Expose a single public entry point (e.g., a function or class method) that takes a normalized request object with `message_text`, `metadata`, and `context`.

- **Validate required top-level fields**
  - Check that `message_text` (string), `metadata` (object), and `context` (object) are present.
  - If validation fails, return a structured error response (see error model in `ORCHESTRATOR_INTERFACE.md`).

- **Call Router dependency**
  - Invoke an injected Router callable with the normalized input.
  - Receive Router output aligned with the conceptual `router_output.schema.json`.

- **Branch by `task_type`**
  - Inspect the Router’s `task_type`.
  - Decide between:
    - direct GILE workflow (`translate`, `rewrite`, `validate`),
    - Planner / Reply / GILE workflow (`document_draft`, `reply_draft`),
    - Planner‑only workflow (`document_plan`),
    - clarification workflow (`needs_clarification`).

- **Call Planner dependency when required**
  - For `document_draft`, `reply_draft`, and `document_plan`:
    - Invoke the Planner with the Router’s `handoff_payload`.
  - For other `task_type` values, **do not** call the Planner.

- **Call Reply dependency when required**
  - For `document_draft` and `reply_draft`:
    - Invoke the Reply Agent with the Planner output.
  - For `document_plan` and other `task_type` values, **do not** call the Reply Agent.

- **Call GILE dependency when required**
  - For workflows that require final Georgian institutional text (e.g., `document_draft`, `reply_draft`, and direct language tasks):
    - Invoke GILE using the appropriate reply → GILE handoff contract.
  - For `document_plan` and pure clarification workflows, **do not** call GILE.

- **Return structured response**
  - Construct an `orchestrator_response` object matching the output contract in `ORCHESTRATOR_INTERFACE.md`, including:
    - `status`,
    - `workflow` (task_type, route label, steps_executed),
    - `artifacts` (selected intermediate outputs),
    - `final_output` (text or plan for success).

- **Return explicit error blocks on failure**
  - On validation errors or invalid agent outputs:
    - Set `status = "error"`,
    - populate an `error` block with a high-level `code` and `message`,
    - include any safe intermediate artifacts when helpful.

The first implementation should aim to be **small, explicit, and predictable**, with no hidden behavior beyond these responsibilities.

---

### Dependency model

The orchestrator should treat the Router, Planner, Reply Agent, and GILE as **injectable dependencies**:

- Each dependency is represented as a **callable or interface object** that:
  - accepts a well-defined input payload, and
  - returns a structured result aligned with the corresponding schema/contract.

- At construction or initialization time, the orchestrator module/function should receive:
  - a Router callable,
  - a Planner callable,
  - a Reply callable,
  - a GILE callable.

- In early stages, these callables may be:
  - simple stub functions,
  - test doubles or mocks,
  - or thin wrappers around future real implementations.

This model avoids hard-coding any particular implementation and makes it easy to swap in real components as they are developed.

---

### Suggested internal helper functions

To keep the main orchestration logic clear and testable, the v1 implementation should introduce a small set of **internal helper functions** (names are indicative, not prescriptive):

- **`validate_input`**
  - Check presence and basic shape of `message_text`, `metadata`, and `context`.
  - On failure, build and return an error response without calling any agents.

- **`validate_router_output`**
  - Perform minimal structural checks on the Router result (e.g., `task_type`, `handoff_payload`).
  - Map validation failures to `invalid_router_output` errors.

- **`validate_planner_output`**
  - Perform minimal structural checks on the Planner result (e.g., `intent`, `document_format`, `sections`).
  - Map validation failures to `invalid_planner_output` errors.

- **`validate_reply_output`**
  - Perform minimal structural checks on the Reply result (e.g., `draft_text`, `draft_type`).
  - Map validation failures to `invalid_reply_output` errors.

- **`build_error_response`**
  - Construct a standardized error response object using:
    - an error `code` (e.g., `invalid_router_output`, `gile_call_failed`),
    - a human-readable `message`,
    - any available artifacts to aid debugging.

Additional small helpers may be introduced as needed for assembling the `workflow` and `artifacts` blocks, as long as they do not change the public interface or architecture.

---

### What v1 should NOT include

The first Python implementation **must not** attempt to solve everything. Specifically, v1 should **exclude**:

- Real model calls (LLM or other heavy inference)
- Async orchestration (no background tasks, queues, or event loops)
- Persistence (no databases, files, or long-term state)
- Retries or backoff strategies
- Telemetry, metrics, or logging infrastructure beyond minimal debugging
- Prompt loading or templating logic (these live under `prompts/` and can be integrated later)
- Connector integrations (e.g., APIs, message buses, external systems)

V1 should focus solely on **wiring, validation, branching, and response shaping** using injected dependencies.

---

### Testability

The orchestrator’s dependency-injection design makes the v1 implementation straightforward to test:

- Each dependency (Router, Planner, Reply, GILE) can be replaced by:
  - deterministic stubs that return fixed schema‑compatible outputs, or
  - mocks that record how they were called.

- Tests can:
  - verify branching logic based on different `task_type` values,
  - confirm that invalid outputs from a stubbed agent produce the correct error code and `status = "error"`,
  - ensure that the `workflow` and `artifacts` sections are populated as expected for each path.

Because there are no real model calls, async behavior, or external integrations in v1, tests can run quickly and deterministically.

---

### Status

This document is the **final planning step** before writing `runtime/orchestration/orchestrator.py`. The eventual Python implementation must:

- conform to `ORCHESTRATOR_INTERFACE.md`,
- respect the contracts in `agents/HANDOFF_CONTRACTS.md` and `agents/schemas/`, and
- preserve the existing separation of responsibilities between Router, Document Planner, Reply Agent, GILE, and the Orchestrator.

No Python code has been written yet; the next step is to implement `orchestrator.py` according to this plan.

