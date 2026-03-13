## Reply Agent v1 Specification

### 1. Purpose

Reply Agent v1 creates the **initial draft response** based on a structured plan, the source message, and relevant context. It turns the planner’s sections and intents into a coherent draft that is then handed to **GILE** for institutional Georgian translation, rewrite, and refinement.

### 2. Role in the System

Reply Agent v1 participates in the following high‑level flow:

Incoming message  
→ **Router Agent** (classifies and routes)  
→ **Document Planner** (designs structure and sections)  
→ **Reply Agent** (creates the initial draft)  
→ **GILE** (translation / rewrite / refinement / validation)  
→ **Institutional Georgian output**

The Reply Agent produces **draft content**, not final institutional Georgian output. Any externally visible institutional Georgian text must be produced or finalized by **GILE**.

### 3. Scope

Reply Agent v1 **is responsible for**:

- **Following the planner’s structure** – respect `plan_type`, sections, and ordering.
- **Drafting complete initial content** – produce a coherent draft that covers all required sections.
- **Preserving source meaning and instructions** – honor user intent, planner guidance, and constraints.
- **Preparing output for GILE handoff** – clearly indicate how GILE should treat the draft (e.g., translate, rewrite).

Reply Agent v1 **must not**:

- Perform final institutional Georgian refinement or validation.
- Replace GILE translation, rewrite, terminology enforcement, or validation.
- Perform routing decisions (this belongs to the Router Agent).
- Perform document planning or define structure (this belongs to the Document Planner).

It is a **drafting component**, not a planner, router, or language engine.

### 4. Input Contract (v1)

Reply Agent v1 expects a structured input aligned with the planner’s output:

```json
{
  "plan_type": "string – e.g., reply_structure | document_structure | plan_only",
  "sections": [
    {
      "section_id": "string – identifier matching the planner output",
      "title": "optional short label",
      "purpose": "string – what this section should accomplish",
      "required": "boolean – whether this section must be present"
    }
  ],
  "draft_instructions": {
    "tone": "optional description of desired tone",
    "length": "optional guidance (e.g., short, detailed)",
    "style_notes": "optional structure or emphasis notes",
    "additional": "optional free‑form drafting guidance"
  },
  "source_message": "string – primary user or system message to respond to",
  "context": {
    "conversation_history": "optional structured data",
    "related_documents": "optional structured data",
    "constraints": "optional policies, limitations, or caveats"
  }
}
```

### 5. Output Contract (v1)

Reply Agent v1 returns a draft and metadata suitable for GILE handoff:

```json
{
  "draft_text": "string – the full drafted content following the plan",
  "draft_language": "string – e.g., EN or KA, describing the main language of the draft",
  "draft_type": "string – e.g., reply | document",
  "requires_gile": "boolean – whether this draft must be processed by GILE before use",
  "gile_action": "string – e.g., translate | rewrite | validate, indicating the expected GILE operation",
  "notes_for_gile": "string – optional notes to GILE about tone, terminology, or risks"
}
```

- **`draft_text`** – the initial, non‑final content created by the Reply Agent.  
- **`draft_language`** – clarifies the language of the draft for GILE.  
- **`draft_type`** – aligns with drafting mode (e.g., reply vs. document).  
- **`requires_gile`** – should be `true` for any external institutional Georgian use.  
- **`gile_action`** – suggests the primary way GILE should process the draft.  
- **`notes_for_gile`** – carries additional guidance without duplicating GILE’s logic.

### 6. Drafting Modes

Reply Agent v1 supports simple drafting modes:

- **`reply`** – single message replies (often shorter, conversational, or transactional).
- **`document`** – multi‑section documents (e.g., policies, reports, formal letters).

The **draft_type** field should reflect which mode was used.

### 7. Drafting Rules

Practical drafting rules for v1:

- **Follow section order** from the planner’s `sections` array.
- **Satisfy section intent** – each section should fulfill its `purpose`.
- **Preserve factual meaning** from the `source_message` and `context`; do not alter facts.
- **Do not invent facts** – if information is missing, acknowledge limitations instead of fabricating details.
- **Indicate GILE’s role** – use `requires_gile` and `gile_action` to show whether GILE should translate, rewrite, or validate.
- **Reflect insufficient input** – when information is incomplete or ambiguous, surface this in the draft rather than guessing.

The Reply Agent may produce drafts in English or provisional Georgian, but **final institutional Georgian** must always be produced or finalized by GILE.

### 8. Non‑Goals

Reply Agent v1 must **not**:

- Bypass GILE when institutional Georgian output is required.
- Perform translation, institutional rewrite, terminology enforcement, retrieval, or validation itself.
- Override or redesign the structure provided by the Document Planner.
- Make routing decisions or select workflows.
- Encode business‑specific approval or escalation logic that belongs elsewhere.

It is intended solely to **instantiate the planner’s structure as a draft** ready for GILE.

### 9. Examples (Planner Input → Reply Output Behavior)

#### Example 1 – Complaint reply

- **Planner input (simplified)**:

  - `plan_type`: `reply_structure`  
  - Sections: `greeting`, `acknowledgment`, `resolution`, `closing`  
  - Source message: customer complaint about delayed delivery.

- **Reply Agent behavior**:

  - Produces `draft_text` with all four sections present in order.  
  - Sets `draft_language` to `EN`.  
  - Sets `draft_type` to `reply`.  
  - Sets `requires_gile` to `true`, `gile_action` to `translate` (for institutional Georgian).

#### Example 2 – Policy document draft

- **Planner input (simplified)**:

  - `plan_type`: `document_structure`  
  - Sections: `introduction`, `eligibility`, `expectations`, `security`, `review`.  
  - Source message: request to create a remote work policy.

- **Reply Agent behavior**:

  - Produces a structured `draft_text` covering each section’s `purpose`.  
  - Sets `draft_language` to `EN`.  
  - Sets `draft_type` to `document`.  
  - Sets `requires_gile` to `true`, `gile_action` to `translate` or `rewrite` (depending on target language and quality needs).

#### Example 3 – Limited information reply

- **Planner input (simplified)**:

  - `plan_type`: `reply_structure`  
  - Sections: `greeting`, `acknowledgment`, `clarification_request`.  
  - Source message: very vague user question without details.

- **Reply Agent behavior**:

  - Produces `draft_text` that acknowledges the message and explicitly asks for missing information, without inventing details.  
  - Sets `draft_language` to `EN`.  
  - Sets `draft_type` to `reply`.  
  - Sets `requires_gile` to `true`, `gile_action` to `translate` if the final reply must be in institutional Georgian.

### 10. Status

This document defines the **Reply Agent v1 specification** only. No runtime implementation, classes, or API clients exist yet in this repository; drafting logic will be implemented later in alignment with this contract, while **GILE remains the external language layer for institutional Georgian**.

