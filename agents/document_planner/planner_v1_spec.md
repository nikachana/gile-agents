## Document Planner v1 Specification

### 1. Purpose

Document Planner v1 determines the **structure** of responses and documents **before drafting occurs**. It focuses on what sections are needed, in what order, and with what intent, so that downstream drafting and GILE can operate against a clear plan.

### 2. Role in the System

In the overall system, the planner participates in the following high‑level flow:

Incoming message  
→ **Router Agent** (classifies and routes)  
→ **Document Planner** (designs structure and sections)  
→ **Reply Agent** (creates the initial draft)  
→ **GILE** (translation / rewrite / refinement / validation)  
→ **Institutional Georgian output**

The Document Planner produces a **structured plan**, not final text. It defines the skeleton and intent of the response or document, which the Reply Agent and GILE then turn into fully written, institutional Georgian output.

### 3. Scope

Planner v1 **is responsible for**:

- Determining **document/response structure** (e.g., headings, sections, ordering).
- Defining **required sections** and marking which are mandatory vs. optional.
- Defining **section intent** – what each section should achieve or cover.
- Passing **drafting instructions** to the Reply Agent or other drafting workflows.

Planner v1 **must not**:

- Write final text or full sentences intended for external use.
- Perform institutional Georgian rewriting, refinement, or validation.
- Replicate any of GILE’s translation, rewrite, terminology, retrieval, or validation behavior.

It is a **planning component**, not a language generator.

### 4. Input Contract (v1)

Planner v1 expects a simple JSON input describing the task and context:

```json
{
  "task_type": "string – e.g., reply_draft | document_draft | document_plan",
  "message_text": "string – primary user or system message to respond to",
  "metadata": {
    "channel": "optional string",
    "locale": "optional string",
    "role": "optional string (e.g., user, staff)",
    "tags": ["optional", "string", "array"]
  },
  "context": {
    "conversation_history": "optional structured data",
    "related_documents": "optional structured data",
    "constraints": "optional policies, tone, or length constraints"
  }
}
```

- **Required**: `task_type`, `message_text`  
- **Optional**: `metadata`, `context`

### 5. Output Contract (v1)

Planner v1 returns a structured plan in JSON:

```json
{
  "plan_type": "string – one of reply_structure | document_structure | plan_only",
  "document_format": "string – optional institutional format, e.g., official_letter",
  "sections": [
    {
      "section_id": "string – stable identifier, e.g., intro, summary, actions",
      "title": "optional short label for internal use",
      "purpose": "string – description of what this section should accomplish",
      "required": "boolean – whether this section must be present"
    }
  ],
  "draft_instructions": {
    "tone": "optional description of desired tone (e.g., formal, neutral)",
    "length": "optional guidance (e.g., short, detailed)",
    "style_notes": "optional notes about structure, emphasis, or ordering",
    "additional": "optional free‑form guidance for the drafting agent"
  }
}
```

Each **section** must at least specify a `section_id` and `purpose`. The optional `document_format` field allows the planner to declare formats such as `"official_letter"`, `"meeting_minutes"`, or `"protocol"`. Titles and additional flags are internal aids for drafting, not final text.

### 6. Supported Plan Types

Planner v1 recognizes the following `plan_type` values:

- **`reply_structure`** – structure for a single reply message (e.g., greeting, acknowledgment, main content, closing).
- **`document_structure`** – structure for multi‑section documents (e.g., policy, report, letter).
- **`plan_only`** – outline or plan without a commitment to immediate drafting.

These plan types describe **how the response is organized**, not the exact language used.

### 7. Planning Rules

High‑level mapping rules between tasks and plan types:

- `reply_draft` tasks **produce** a `reply_structure` plan.
- `document_draft` tasks **produce** a `document_structure` plan.
- `document_plan` tasks **produce** a `plan_only` plan (outline/sections only).

Additional rules:

- The planner describes **intent and structure**, not full sentences or finalized wording.
- Section `purpose` fields should focus on **what to cover**, not on how to phrase it.
- Any examples or hints are for internal guidance; **GILE remains responsible** for institutional Georgian wording and refinement.

### 8. Examples

#### Example 1 – Simple reply structure for a complaint

```json
{
  "plan_type": "reply_structure",
  "sections": [
    {
      "section_id": "greeting",
      "title": "Greeting",
      "purpose": "Politely greet the customer and acknowledge the message.",
      "required": true
    },
    {
      "section_id": "acknowledgment",
      "title": "Issue acknowledgment",
      "purpose": "Summarize the complaint and show understanding of the issue.",
      "required": true
    },
    {
      "section_id": "resolution",
      "title": "Resolution",
      "purpose": "Explain the action taken or proposed to address the complaint.",
      "required": true
    },
    {
      "section_id": "closing",
      "title": "Closing",
      "purpose": "Close with appreciation and invite further questions if needed.",
      "required": true
    }
  ],
  "draft_instructions": {
    "tone": "polite, professional, empathetic",
    "length": "short",
    "style_notes": "Focus on clarity and reassurance.",
    "additional": ""
  }
}
```

#### Example 2 – Policy document structure

```json
{
  "plan_type": "document_structure",
  "sections": [
    {
      "section_id": "introduction",
      "title": "Introduction",
      "purpose": "State the purpose and scope of the remote work policy.",
      "required": true
    },
    {
      "section_id": "eligibility",
      "title": "Eligibility",
      "purpose": "Describe which roles and employees are eligible for remote work.",
      "required": true
    },
    {
      "section_id": "expectations",
      "title": "Expectations",
      "purpose": "Outline working hours, availability, and performance expectations.",
      "required": true
    },
    {
      "section_id": "security",
      "title": "Security",
      "purpose": "Describe information security and data protection requirements.",
      "required": true
    },
    {
      "section_id": "review",
      "title": "Review and changes",
      "purpose": "Explain how the policy will be reviewed and updated.",
      "required": false
    }
  ],
  "draft_instructions": {
    "tone": "formal, institutional",
    "length": "detailed",
    "style_notes": "Use clear headings and logical ordering.",
    "additional": ""
  }
}
```

#### Example 3 – Plan‑only outline for a guidance note

```json
{
  "plan_type": "plan_only",
  "sections": [
    {
      "section_id": "summary",
      "title": "Summary",
      "purpose": "Summarize the main guidance in 2–3 key ideas.",
      "required": true
    },
    {
      "section_id": "steps",
      "title": "Key steps",
      "purpose": "List the main steps the reader should follow.",
      "required": true
    },
    {
      "section_id": "caveats",
      "title": "Caveats",
      "purpose": "Highlight important limitations or risks to consider.",
      "required": false
    }
  ],
  "draft_instructions": {
    "tone": "neutral, clear",
    "length": "medium",
    "style_notes": "Emphasize practical, actionable structure; no full drafting required at this stage.",
    "additional": ""
  }
}
```

### 9. Status

This document defines the **Document Planner v1 specification** only. No runtime implementation, classes, or API clients exist yet in this repository; planning logic will be implemented later in alignment with this contract, while GILE remains the external language layer.

