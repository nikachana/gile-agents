# Schema artifacts for v1 agent pipeline

### Purpose

This directory contains **documentation-level JSON schema artifacts** for the v1 `gile-agents` pipeline. They define the canonical shape of the data exchanged between:

- `Router Agent` → `Document Planner`
- `Document Planner` → `Reply Agent`
- `Reply Agent` → `GILE`

These schemas:

- mirror the handoff contracts defined in `agents/HANDOFF_CONTRACTS.md`
- are **canonical for v1** but **not yet enforced at runtime**
- should be treated as the source of truth when evolving or reviewing agent handoffs

No validation or implementation logic is provided here; these files are purely descriptive artifacts intended for documentation, review, and future implementation.

