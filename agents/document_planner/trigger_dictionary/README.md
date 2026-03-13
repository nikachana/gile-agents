## Georgian Bureaucratic Trigger Dictionary (v1)

This directory contains the **Georgian Bureaucratic Trigger Dictionary** used by the **Document Planner** to assist with **intent detection** for institutional documents.

- **Purpose**: capture common Georgian institutional phrases that strongly suggest a particular **document intent** (communication, decision, documentation, confirmation, analysis).
- **Scope**: provide lightweight, configurable hints that complement (but do not replace) the planner’s reasoning and the formal **intent taxonomy**.

### Georgian Institutional Phrases and Intent

Certain bureaucratic phrases in Georgian reliably signal what kind of document or action is being requested, for example:

- Communication‑oriented phrases that introduce or deliver information to recipients.
- Decision‑oriented phrases that impose duties or formalize resolutions.
- Documentation‑oriented phrases that summarize meeting processes or outcomes.
- Confirmation‑oriented phrases that attest to facts or statuses.
- Analysis‑oriented phrases that introduce explanations, remarks, or evaluative commentary.

These triggers are recorded in `triggers.json` as **phrase → intent** hints with an associated confidence level.

### How the Planner Uses Triggers

The Document Planner:

- Scans the **message text** for known trigger phrases from `triggers.json`.
- Combines matched triggers (and their **intent** / **confidence**) with:
  - the **intent taxonomy** (`intent_taxonomy.json`),
  - Router‑provided task type and metadata,
  - broader contextual reasoning.
- Uses the resulting intent signal to select an appropriate **document format** (e.g., `official_letter`, `order`, `meeting_minutes`, `certificate`, `memo`) and to construct a **section‑level plan**.

Triggers are **hints only**. They do not hard‑code outcomes and they do not replace higher‑level reasoning or institutional policy; they simply help the planner converge more quickly on the correct intent and format before drafting begins.

