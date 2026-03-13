## Documentation Conventions

This repository is **documentation‑first**. The goal is to keep behavior and responsibilities explicit and easy to understand.

### Ownership of Documentation

- **Each agent directory must include its own `README.md`** describing:
  - purpose and responsibilities,
  - expected inputs and outputs,
  - what is intentionally not implemented yet.
- **Cross‑cutting rules** (e.g., integration with GILE, shared patterns) belong in **top‑level docs** under `docs/` or in the root files.

### Separation from GILE

- Agent documentation and code **must not duplicate GILE logic** (translation, rewrite, refinement, validation).
- Internal reasoning and planning may be done in **English**, even when the final output is Georgian.
- **All final institutional Georgian output must go through GILE**, never directly from an agent.

### Style and Maintenance

- Keep documents **short, explicit, and focused**.
- Update documentation **whenever behavior or responsibilities change**.
- Prefer describing **contracts and boundaries** over low‑level implementation details.

