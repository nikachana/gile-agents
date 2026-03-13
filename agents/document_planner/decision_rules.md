## Document Planner Decision Rules (v1)

This document describes how the **Document Planner** selects an institutional document format based on **recipient type**, **intent type**, **trigger words**, **structural hints**, and **institutional context**. It is a design artifact only; no runtime logic is implemented yet.

### 1. Inputs to Format Selection

Planner v1 may consider the following inputs when choosing a format:

- **Recipient type** – internal vs. external, individual vs. organization.
- **Intent type** – high‑level institutional intent derived from `intent_taxonomy.json`.
- **Trigger words** – explicit phrases in the message (e.g., “official letter”, “order”, “minutes”, “certificate”, “memo”).
- **Structural hints** – references to sections, signatures, decisions, or meeting elements.
- **Institutional context** – channel, role (citizen, staff), and domain (HR, legal, administration).

### 2. Intent Taxonomy and Default Formats

Planner v1 uses the following **intent → default format** mapping:

- **communication** → `official_letter`
- **decision** → `order`
- **documentation** → `meeting_minutes`
- **confirmation** → `certificate`
- **analysis** → `memo`

The default format may be overridden only when strong conflicting signals exist (e.g., explicit reference to a different format).

### 3. Recipient‑Based Rules

- **External recipients** (citizens, other institutions, companies):
  - Prefer **`official_letter`** when the task is communication‑oriented and mentions sending or responding formally.
  - Use **`certificate`** when the institution is asked to formally confirm a fact or status.
- **Internal recipients** (staff, departments, internal committees):
  - Prefer **`memo`** for short internal guidance or updates.
  - Use **`order`** when the request clearly involves a binding internal decision or directive.
  - Use **`meeting_minutes`** when documenting an internal meeting.

Recipient type **refines** but does not replace the intent taxonomy.

### 4. Trigger Word Rules

When specific trigger words appear, they can strongly suggest a format:

- Words like **“official letter”, “formal letter”, “response to citizen”** → prefer `official_letter`.
- Words like **“order”, “decree”, “administrative decision”** → prefer `order`.
- Words like **“minutes”, “protocol of meeting”, “meeting notes”** → prefer `meeting_minutes`.
- Words like **“certificate”, “confirm employment”, “proof of status”** → prefer `certificate`.
- Words like **“memo”, “internal note”, “inform staff”** → prefer `memo`.

Trigger words should be weighed together with intent and recipient type; they do not override institutional constraints.

### 5. Structural Hint Rules

Certain structural expectations also inform format selection:

- Requests mentioning **agenda, participants, decisions, action items** → strong signal for `meeting_minutes`.
- Requests mentioning **numbered articles, legal basis, effective date** → strong signal for `order`.
- Requests mentioning **header, subject line, greeting, closing** in external communication → strong signal for `official_letter`.
- Requests mentioning **certificate number, validity period, date and place of issue** → strong signal for `certificate`.
- Requests mentioning **short internal note, key points, actions required** → strong signal for `memo`.

Structural hints help the planner load an appropriate **section structure** from the format library.

### 6. Institutional Context Rules

Planner v1 may also consider:

- **Channel**:
  - Citizen‑facing portals and outward‑facing channels → bias toward `official_letter` or `certificate`.
  - Internal systems and staff‑only channels → bias toward `memo`, `order`, or `meeting_minutes`.
- **Role**:
  - Requests originating from staff about internal procedures → often `memo`, `order`, or `meeting_minutes`.
  - Requests from citizens for proof or confirmation → often `certificate`.

Context is advisory and should be combined with intent and trigger words.

### 7. Resolution Strategy

When multiple signals conflict:

1. **Check explicit trigger words** for a precise format name (e.g., “prepare meeting minutes” → `meeting_minutes`).
2. If no explicit trigger, **use intent taxonomy** to choose the default format.
3. Use **recipient type and structural hints** to confirm or mildly adjust the choice.
4. If ambiguity remains, planner v1 may:
   - choose the **default format** from the intent taxonomy, and
   - mark the plan with notes indicating uncertainty for the Reply Agent and GILE.

Planner v1 should **not** silently invent new formats or mix incompatible structures.

### 8. Boundaries

- Format selection is a **planning concern**, not a language concern.
- The planner:
  - selects format IDs,
  - loads structures from `format_library/`,
  - uses section definitions from `section_vocabulary/`.
- The planner **does not**:
  - perform translation, rewrite, or validation,
  - encode institution‑specific legal content or final wording (left to GILE and policy owners).

