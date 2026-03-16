# Runtime layer for `gile-agents`

### Purpose

This directory is reserved for the **executable runtime implementations** of the agents defined in this repository. It complements, but does not replace, the existing architectural specifications.

- `agents/` – contains the **architectural specifications, contracts, and documentation** for the Router Agent, Document Planner, Reply Agent, and GILE-related boundaries.
- `runtime/` – will contain the **concrete runtime implementations** of those agents (code, adapters, and integration glue).
- `prompts/` – will contain **LLM prompt templates and prompt-building logic** that the runtime layer uses.
- `tests/` – will contain **evaluation and regression tests** for agent behavior, contracts, and pipeline stability.

This separation keeps the **architecture and contracts in `agents/` independent from any specific implementation**, allowing the team to evolve runtime code, prompts, and tests without rewriting the core design documents or handoff contracts.

At this stage, `runtime/` only defines structure; no executable code has been added yet.

