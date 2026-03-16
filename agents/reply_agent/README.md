## Reply Agent

### Purpose

The Reply Agent creates the **initial draft response** based on an existing plan, source message, and context. It focuses on drafting **contentful replies** that can then be refined and institutionalized by GILE.

### Likely Future Inputs

- Plan and structure provided by the Document Planner or other planning agent.
- Source message and relevant conversation history.
- Additional context and constraints (policies, tone requirements, templates).
- Explicit reply requirements (length, level of detail, target audience).

### Likely Future Outputs

- Draft response in **English or Georgian**, suitable for handoff to GILE.
- Optional notes or annotations indicating where GILE should translate, rewrite, or refine.

### Reply Agent v1 documentation artifacts

The Reply Agent v1 is documented through the following artifacts:

- `reply_v1_spec.md` – defines Reply Agent v1 scope, responsibilities, and interaction with the planner and GILE.
- `../HANDOFF_CONTRACTS.md` – specifies the planner → reply and reply → GILE handoff contracts in the overall pipeline.
- `../schemas/reply_output.schema.json` – JSON Schema describing the structured v1 output that GILE consumes.

### Boundaries and Non‑Goals

- **Not implemented yet** – this directory currently documents intent and contracts only; no runtime logic is present.
- Must **not** replace GILE’s responsibilities for:
  - translation to institutional Georgian,
  - rewrite and refinement,
  - terminology enforcement and validation.
- Any **final institutional Georgian output** must be produced or finalized by GILE, not directly by the Reply Agent.

