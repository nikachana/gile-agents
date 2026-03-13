## Integration with GILE

GILE is treated as an **external language engine**. This repository does not embed GILE logic; it only **calls** GILE as a service.

### Integration Methods

Expected integration mechanisms include:

- **HTTP API**
  - Using endpoints such as `POST /translate`, `POST /rewrite`, `POST /validate`.
- **MCP tools**
  - Tools such as `gile.translate`, `gile.rewrite`.
- **Future adapters**
  - Additional adapters or client libraries may be added later, but they must continue to treat GILE as an external component.

### Conceptual Contract

- **Agents**:
  - Produce **draft intent and content** (often in English, sometimes in Georgian).
  - Decide when and how to call GILE.
  - Orchestrate multi‑step workflows around GILE.
- **GILE**:
  - Produces **institutional Georgian output** via translation, rewrite, refinement, and validation.
  - Enforces institutional terminology and style.

Agents **must not bypass GILE** when generating final official Georgian text. Any output that is externally visible as institutional Georgian should have been produced or finalized by GILE.

