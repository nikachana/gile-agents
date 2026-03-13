# Agent Handoff Contracts

### Purpose

This document defines the canonical data contracts exchanged between the `Router Agent`, `Document Planner`, `Reply Agent`, and `GILE` in the `gile-agents` pipeline. It is documentation only and does not change runtime behavior.

### Pipeline overview

Incoming request  
↓  
Router Agent  
↓  
Document Planner  
↓  
Reply Agent  
↓  
GILE  
↓  
Institutional Georgian output

---

### 1. Router → Document Planner contract

#### 1.1 Purpose

Define the normalized classification output from the `Router Agent` that the `Document Planner` consumes to detect intent, choose document format, and plan sections. The Router focuses on **workflow classification**, not document structure.

#### 1.2 Required fields

- **task_type**: High-level workflow/category label (e.g. `document_draft`, `document_plan`, `reply_draft`).
- **route_to**: Target downstream pipeline or agent group (e.g. `document_planner_v1`).
- **confidence**: Numeric confidence score in \[0, 1].
- **reasoning_summary**: Short natural-language justification for the routing decision.
- **handoff_payload**: Payload forwarded to the `Document Planner` (see below).

Within **handoff_payload**:

- **message_text**: Raw or lightly-normalized user request text.
- **metadata**: Object with known non-text attributes (e.g. channel, user role, department).
- **context**: Object describing any contextual artifacts (e.g. previous messages, case IDs).

#### 1.3 Optional fields

- **task_subtype**: More granular categorization under `task_type` (e.g. `disciplinary_order`).
- **router_version**: Identifier of the router configuration/model used.
- **routing_alternatives**: Optional array of fallback or alternative routing hypotheses.

Within **handoff_payload**:

- **attachments**: List of attachment descriptors available to downstream agents.
- **locale_hint**: Hint about source language or expected output locale.

#### 1.4 JSON schema (conceptual)

```json
{
  "task_type": "string",
  "route_to": "string",
  "confidence": 0.0,
  "reasoning_summary": "string",
  "handoff_payload": {
    "message_text": "string",
    "metadata": {
      "...": "..."
    },
    "context": {
      "...": "..."
    },
    "attachments": [
      {
        "id": "string",
        "type": "string",
        "name": "string"
      }
    ],
    "locale_hint": "string"
  },
  "task_subtype": "string",
  "router_version": "string",
  "routing_alternatives": [
    {
      "task_type": "string",
      "route_to": "string",
      "confidence": 0.0
    }
  ]
}
```

#### 1.5 JSON example

```json
{
  "task_type": "document_draft",
  "task_subtype": "employment_confirmation",
  "route_to": "document_planner_v1",
  "confidence": 0.92,
  "reasoning_summary": "The request asks for a formal written confirmation addressed to an external organization.",
  "router_version": "router-ge-v1",
  "handoff_payload": {
    "message_text": "Please prepare an official employment confirmation letter for our employee, confirming their position and salary.",
    "metadata": {
      "channel": "web_portal",
      "requester_role": "HR_specialist",
      "department": "Human_Resources"
    },
    "context": {
      "employee_id": "EMP-12345",
      "case_id": "CASE-2026-001"
    },
    "attachments": [],
    "locale_hint": "ka-GE"
  },
  "routing_alternatives": [
    {
      "task_type": "document_plan",
      "route_to": "document_planner_v1",
      "confidence": 0.65
    }
  ]
}
```

---

### 2. Document Planner → Reply Agent contract

#### 2.1 Purpose

Define the structured planning output from the `Document Planner` that the `Reply Agent` consumes to generate the **first full draft**. The Planner focuses on **intent detection, format selection, and section planning**, not language refinement.

#### 2.2 Required fields

- **intent**: Canonical intent label summarizing the user’s underlying goal (e.g. `communication`, `decision`, `documentation`, `confirmation`, `analysis`).
- **document_format**: Chosen document format type (e.g. `official_letter`, `order`, `meeting_minutes`).
- **confidence**: Numeric confidence score in \[0, 1] for the plan as a whole.
- **reasoning_summary**: Short explanation of how the intent and document format were chosen.
- **sections**: Ordered array describing the high-level structure of the document.
- **draft_instructions**: Guidance for the `Reply Agent` on tone, style, and constraints.
- **source_payload**: Opaque payload that preserves the upstream Router data and any relevant context.

Within **sections** (each element):

- **id**: Stable identifier for the section (e.g. `intro`, `body_requirements`).
- **title**: Human-readable section title or label.
- **purpose**: One-sentence description of what this section should achieve.
- **required**: Boolean flag indicating whether the section must appear in the draft.

#### 2.3 Optional fields

- **format_variant**: Variant of the document format (e.g. `strict_official`, `informal_internal`).
- **risk_flags**: Array of flags indicating legal/compliance sensitivities.
- **dependent_on_sections**: Section-level dependencies or ordering constraints.

Within **sections** (optional per section):

- **hints**: Style/content hints for the section.
- **examples**: Short illustrative snippets (not to be copied verbatim).

Within **draft_instructions**:

- **tone** (required): Target tone (e.g. `formal_institutional`, `neutral`, `friendly_professional`).
- **language** (required): Expected drafting language before GILE (e.g. `ka-GE`).
- **constraints** (optional): Special constraints such as length limits or mandatory phrases.

#### 2.4 JSON schema (conceptual)

```json
{
  "intent": "string",
  "document_format": "string",
  "format_variant": "string",
  "confidence": 0.0,
  "reasoning_summary": "string",
  "risk_flags": ["string"],
  "sections": [
    {
      "id": "string",
      "title": "string",
      "purpose": "string",
      "required": true,
      "hints": ["string"],
      "examples": ["string"],
      "dependent_on_sections": ["string"]
    }
  ],
  "draft_instructions": {
    "tone": "string",
    "language": "string",
    "constraints": ["string"]
  },
  "source_payload": {
    "...": "..."
  }
}
```

#### 2.5 JSON example

```json
{
  "intent": "confirmation",
  "document_format": "official_letter",
  "format_variant": "strict_official",
  "confidence": 0.89,
  "reasoning_summary": "The user is asking for a formal employment confirmation letter to be sent to an external party.",
  "risk_flags": ["employment_information", "salary_information"],
  "sections": [
    {
      "id": "header",
      "title": "Letter Header",
      "purpose": "Identify the institution, date, and reference details.",
      "required": true,
      "hints": ["Use official institution header structure."],
      "examples": ["Institution name, address, date, reference number."]
    },
    {
      "id": "body_confirmation",
      "title": "Employment Confirmation Body",
      "purpose": "Confirm the employee’s position, tenure, and salary as needed.",
      "required": true,
      "hints": ["Avoid unnecessary personal information.", "Keep salary phrasing precise."],
      "examples": ["We hereby confirm that..."]
    },
    {
      "id": "closing",
      "title": "Closing and Signature",
      "purpose": "Provide formal closing, contact details, and signature block.",
      "required": true,
      "hints": ["Use institutional closing phrasing."],
      "examples": []
    }
  ],
  "draft_instructions": {
    "tone": "formal_institutional",
    "language": "ka-GE",
    "constraints": [
      "Do not invent salary figures.",
      "Do not include confidential personal details beyond what is provided."
    ]
  },
  "source_payload": {
    "router_output": {
      "task_type": "document_draft",
      "route_to": "document_planner_v1",
      "confidence": 0.92
    },
    "original_message_text": "Please prepare an official employment confirmation letter for our employee, confirming their position and salary.",
    "context": {
      "employee_id": "EMP-12345",
      "case_id": "CASE-2026-001"
    }
  }
}
```

---

### 3. Reply Agent → GILE contract

#### 3.1 Purpose

Define the drafting output from the `Reply Agent` that the `GILE` component consumes for **language refinement only**. The Reply Agent is responsible for producing a structurally correct draft aligned with the `Document Planner`’s sections; GILE refines language, fluency, and institutional style in Georgian.

#### 3.2 Required fields

- **draft_text**: Full draft produced from the plan, prior to GILE refinement.
- **draft_language**: Language code used for the draft before GILE (e.g. `ka-GE`).
- **draft_type**: Type of draft (e.g. `official_letter`, `order`, `meeting_minutes`).
- **requires_gile**: Boolean indicating whether GILE refinement is required.
- **gile_action**: Requested refinement action when `requires_gile` is true (e.g. `refine_language`, `enforce_institutional_style`).
- **source_plan**: Opaque reference to the planning structure (Planner output) used to generate the draft.

#### 3.3 Optional fields

- **style_hints**: Optional hints for GILE about target style nuances.
- **redaction_notes**: Notes on what must not be added or altered by GILE.
- **segment_map**: Mapping between parts of `draft_text` and plan sections to preserve structure.

#### 3.4 JSON schema (conceptual)

```json
{
  "draft_text": "string",
  "draft_language": "string",
  "draft_type": "string",
  "requires_gile": true,
  "gile_action": "string",
  "style_hints": ["string"],
  "redaction_notes": ["string"],
  "segment_map": [
    {
      "section_id": "string",
      "text_span": {
        "start_char": 0,
        "end_char": 0
      }
    }
  ],
  "source_plan": {
    "...": "..."
  }
}
```

#### 3.5 JSON example

```json
{
  "draft_text": "We hereby confirm that Mr. Giorgi Example has been employed at our institution since 1 January 2020 as a Senior Analyst...",
  "draft_language": "ka-GE",
  "draft_type": "official_letter",
  "requires_gile": true,
  "gile_action": "refine_language",
  "style_hints": [
    "Apply formal institutional Georgian style.",
    "Preserve factual content and structure."
  ],
  "redaction_notes": [
    "Do not introduce or change any numeric values.",
    "Do not add new factual claims."
  ],
  "segment_map": [
    {
      "section_id": "header",
      "text_span": { "start_char": 0, "end_char": 120 }
    },
    {
      "section_id": "body_confirmation",
      "text_span": { "start_char": 121, "end_char": 420 }
    },
    {
      "section_id": "closing",
      "text_span": { "start_char": 421, "end_char": 620 }
    }
  ],
  "source_plan": {
    "intent": "confirmation",
    "document_format": "official_letter",
    "sections": [
      { "id": "header" },
      { "id": "body_confirmation" },
      { "id": "closing" }
    ]
  }
}
```

---

### 4. Required vs optional fields (v1)

For **v1**, the following fields are **mandatory**:

- **Router → Document Planner**
  - **task_type**
  - **route_to**
  - **confidence**
  - **reasoning_summary**
  - **handoff_payload.message_text**
  - **handoff_payload.metadata**
  - **handoff_payload.context**

- **Document Planner → Reply Agent**
  - **intent**
  - **document_format**
  - **confidence**
  - **reasoning_summary**
  - **sections\[ ].id**
  - **sections\[ ].title**
  - **sections\[ ].purpose**
  - **sections\[ ].required**
  - **draft_instructions.tone**
  - **draft_instructions.language**
  - **source_payload**

- **Reply Agent → GILE**
  - **draft_text**
  - **draft_language**
  - **draft_type**
  - **requires_gile**
  - **gile_action**
  - **source_plan**

All other fields documented above are **optional for v1**. They may be progressively adopted by agents without breaking the contracts, as long as the mandatory fields are respected.

---

### 5. Boundary rules

- **Router Agent**
  - Focuses on **workflow classification** and routing only.
  - **Does not choose document format** (e.g. `official_letter` vs `order`); it only labels the task type and route.
  - **Selects the workflow type** via `task_type` (e.g. `document_draft`, `document_plan`, `reply_draft`).

- **Document Planner**
  - Handles **intent detection**, **document format selection**, and **section planning**.
  - **Does not produce final prose**; it defines structure, not full sentences.
  - **Selects the institutional intent** via `intent` using the approved v1 taxonomy (`communication`, `decision`, `documentation`, `confirmation`, `analysis`) and selects `document_format` (e.g. `official_letter`, `order`, `meeting_minutes`, `certificate`, `memo`).

- **Reply Agent**
  - Consumes the plan and produces a **full draft** aligned with the planned sections.
  - **Does not invent its own format structure**; it must respect `document_format` and `sections` from the `Document Planner`.

- **GILE**
  - Performs **language refinement only** (fluency, clarity, institutional Georgian style).
  - **Does not receive reasoning logic or format-selection responsibility**; it treats `draft_text` and `draft_type` as already-structured input.

These boundaries are critical to preserve clear responsibilities and avoid coupling classification, planning, drafting, and refinement.

---

### 6. End-to-end examples

The following are compact, illustrative examples of the full pipeline flow. They are not exhaustive and omit some optional fields for brevity.

#### 6.1 Example: official_letter

- **Router → Document Planner**

```json
{
  "task_type": "document_draft",
  "route_to": "document_planner_v1",
  "confidence": 0.94,
  "reasoning_summary": "User asks for a formal letter addressed to an external organization.",
  "handoff_payload": {
    "message_text": "Draft an official letter confirming that we have received the partner's proposal.",
    "metadata": {
      "requester_role": "Legal_officer"
    },
    "context": {
      "case_id": "CASE-2026-010"
    }
  }
}
```

- **Document Planner → Reply Agent**

```json
{
  "intent": "communication",
  "document_format": "official_letter",
  "confidence": 0.9,
  "reasoning_summary": "The core need is to formally acknowledge receipt of a proposal.",
  "sections": [
    { "id": "header", "title": "Header", "purpose": "Identify institution and date.", "required": true },
    { "id": "body_ack", "title": "Acknowledgement", "purpose": "Formally acknowledge receipt of the proposal.", "required": true },
    { "id": "closing", "title": "Closing", "purpose": "Provide closing and contact details.", "required": true }
  ],
  "draft_instructions": {
    "tone": "formal_institutional",
    "language": "ka-GE"
  },
  "source_payload": {
    "case_id": "CASE-2026-010"
  }
}
```

- **Reply Agent → GILE**

```json
{
  "draft_text": "We hereby confirm receipt of your proposal submitted on 5 March 2026...",
  "draft_language": "ka-GE",
  "draft_type": "official_letter",
  "requires_gile": true,
  "gile_action": "refine_language",
  "source_plan": {
    "intent": "communication",
    "document_format": "official_letter"
  }
}
```

#### 6.2 Example: order

- **Router → Document Planner**

```json
{
  "task_type": "document_draft",
  "route_to": "document_planner_v1",
  "confidence": 0.91,
  "reasoning_summary": "The request asks to issue an internal administrative order.",
  "handoff_payload": {
    "message_text": "Prepare an order assigning the new project manager for the digitalization initiative.",
    "metadata": {
      "requester_role": "Director"
    },
    "context": {
      "initiative_id": "DIGI-2026"
    }
  }
}
```

- **Document Planner → Reply Agent**

```json
{
  "intent": "decision",
  "document_format": "order",
  "confidence": 0.88,
  "reasoning_summary": "User is issuing a formal internal order to assign a project manager.",
  "sections": [
    { "id": "preamble", "title": "Preamble", "purpose": "State legal or institutional basis.", "required": true },
    { "id": "operative_part", "title": "Order Clauses", "purpose": "Specify assignment and responsibilities.", "required": true },
    { "id": "final_provisions", "title": "Final Provisions", "purpose": "Implementation and entry into force.", "required": true }
  ],
  "draft_instructions": {
    "tone": "formal_institutional",
    "language": "ka-GE"
  },
  "source_payload": {
    "initiative_id": "DIGI-2026"
  }
}
```

- **Reply Agent → GILE**

```json
{
  "draft_text": "Based on the internal regulations of the institution, I hereby order...",
  "draft_language": "ka-GE",
  "draft_type": "order",
  "requires_gile": true,
  "gile_action": "refine_language",
  "source_plan": {
    "intent": "decision",
    "document_format": "order"
  }
}
```

#### 6.3 Example: meeting_minutes

- **Router → Document Planner**

```json
{
  "task_type": "document_draft",
  "route_to": "document_planner_v1",
  "confidence": 0.9,
  "reasoning_summary": "User asks to summarize and formalize meeting outcomes as minutes.",
  "handoff_payload": {
    "message_text": "Please prepare official minutes for yesterday's coordination meeting about the new IT system.",
    "metadata": {
      "requester_role": "Coordinator"
    },
    "context": {
      "meeting_date": "2026-03-12"
    }
  }
}
```

- **Document Planner → Reply Agent**

```json
{
  "intent": "documentation",
  "document_format": "meeting_minutes",
  "confidence": 0.87,
  "reasoning_summary": "The goal is to record participants, agenda, and decisions of the meeting.",
  "sections": [
    { "id": "header", "title": "Meeting Header", "purpose": "Date, time, place, participants.", "required": true },
    { "id": "agenda", "title": "Agenda", "purpose": "List agenda items discussed.", "required": true },
    { "id": "discussion", "title": "Discussion Summary", "purpose": "Summarize key points for each agenda item.", "required": true },
    { "id": "decisions", "title": "Decisions and Actions", "purpose": "Record decisions and action items.", "required": true }
  ],
  "draft_instructions": {
    "tone": "formal_institutional",
    "language": "ka-GE"
  },
  "source_payload": {
    "meeting_date": "2026-03-12"
  }
}
```

- **Reply Agent → GILE**

```json
{
  "draft_text": "On 12 March 2026, a coordination meeting was held regarding the new IT system...",
  "draft_language": "ka-GE",
  "draft_type": "meeting_minutes",
  "requires_gile": true,
  "gile_action": "refine_language",
  "source_plan": {
    "intent": "documentation",
    "document_format": "meeting_minutes"
  }
}
```

---

### 7. Status

This document defines the **v1 agent handoff contracts** for the `gile-agents` pipeline. It is a documentation artifact only and **is not yet enforced at runtime**. Future versions may formalize these schemas into code and validation layers without changing the core responsibilities of the Router Agent, Document Planner, Reply Agent, or GILE.

