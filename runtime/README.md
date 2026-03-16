# Runtime layer for `gile-agents`

### Purpose

This directory is reserved for the **executable runtime implementations** of the agents defined in this repository. It complements, but does not replace, the existing architectural specifications.

- `agents/` – contains the **architectural specifications, contracts, and documentation** for the Router Agent, Document Planner, Reply Agent, and GILE-related boundaries.
- `runtime/` – will contain the **concrete runtime implementations** of those agents (code, adapters, and integration glue).
- `prompts/` – will contain **LLM prompt templates and prompt-building logic** that the runtime layer uses.
- `tests/` – will contain **evaluation and regression tests** for agent behavior, contracts, and pipeline stability.

This separation keeps the **architecture and contracts in `agents/` independent from any specific implementation**, allowing the team to evolve runtime code, prompts, and tests without rewriting the core design documents or handoff contracts.

At this stage, `runtime/` only defines structure; no executable code has been added yet.

## Runtime Dependencies

The runtime layer will eventually depend on **callable implementations or adapters** for the following components:

- **Router** – a callable that performs workflow classification and returns structured routing decisions.
- **Document Planner** – a callable that resolves institutional intent, document format, and section plans.
- **Reply Agent** – a callable that generates first drafts from Planner output.
- **GILE** – a callable that performs final Georgian language processing according to the approved contracts.

The `runtime/` layer **executes** the architecture defined under `agents/` (including `agents/HANDOFF_CONTRACTS.md` and `agents/schemas/`), but does **not redefine** it. The Orchestrator design in `runtime/orchestration/ORCHESTRATOR_V1.md` builds directly on those contracts.


