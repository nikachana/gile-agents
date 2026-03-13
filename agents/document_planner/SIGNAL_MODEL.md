# Institutional Document Signal Model

## Purpose

The Document Planner uses a **multi‑signal model** to infer **institutional intent** and select a **document format**. It does **not** rely on a single phrase or keyword; instead, it combines several signal families to arrive at a robust intent and format decision before section planning and drafting.

## Approved v1 Signal Families

Planner v1 considers four primary signal families:

- **Trigger signals**  
  - High‑signal bureaucratic phrases from the Georgian Trigger Dictionary (e.g., `გთხოვთ`, `დავალდეს`, `ვადასტურებთ`).  
  - Provide strong hints about whether the request is communication, decision, documentation, confirmation, or analysis.

- **Recipient signals**  
  - Information about who the document is addressed to (e.g., citizen, external institution, internal staff, internal committee).  
  - Help distinguish external communication (often `official_letter` or `certificate`) from internal communication and decisions (`memo`, `order`, `meeting_minutes`).

- **Action / document verb signals**  
  - Verbs and nouns describing the requested artifact (e.g., “prepare **minutes**”, “issue an **order**”, “draft a **certificate**”, “write an **internal memo**”).  
  - Often provide the **strongest direct evidence** of document type.

- **Institutional context signals**  
  - Channel, role, domain (e.g., HR, legal), and previously known workflow.  
  - Help bias towards appropriate formats when text is ambiguous (e.g., internal HR request → `memo` or `order`).

These signals are combined; none of them alone fully determines the planner’s decision.

## Approved v1 Institutional Intents

Planner v1 works with the following institutional intents:

- `communication`
- `decision`
- `documentation`
- `confirmation`
- `analysis`

These intents map directly into the v1 document formats.

## Canonical v1 Intent → Format Mapping

The canonical mapping between intent and format is:

- **communication** → `official_letter`
- **decision** → `order`
- **documentation** → `meeting_minutes`
- **confirmation** → `certificate`
- **analysis** → `memo`

## Decision Process

Conceptually, the Document Planner follows this process:

1. **Collect signals**  
   - Parse the message text for trigger phrases.  
   - Inspect metadata and context (recipient type, channel, domain).  
   - Identify action verbs and document nouns.  
   - Note any meeting‑ or certification‑related details.

2. **Assign candidate intents**  
   - For each signal, propose one or more candidate intents (e.g., communication, decision).  
   - Use the intent taxonomy and trigger dictionary as reference.

3. **Weight signals**  
   - Apply weights based on signal family and confidence (e.g., strong explicit document verbs vs. weaker generic triggers).  
   - Aggregate scores per candidate intent.

4. **Resolve strongest intent**  
   - Select the intent with the highest combined support, breaking ties with precedence rules (see below).  
   - If still ambiguous, the planner may mark the plan as low‑confidence and request clarification upstream.

5. **Map intent to document format**  
   - Use the canonical v1 mapping (communication → `official_letter`, etc.) to select the document format.  
   - Proceed to load format structure and section vocabulary for planning.

## Signal Precedence Rules

To keep behavior predictable, planner v1 applies these practical precedence rules:

- **Explicit document request beats generic phrasing**  
  - If the user names a specific document type (e.g., “order”, “meeting minutes”, “certificate”, “memo”), this overrides weaker generic communication phrases.

- **Explicit action verb beats weak trigger**  
  - Verbs like “prepare minutes”, “issue an order”, “write a memo”, “issue a certificate” take precedence over generic triggers such as `გთხოვთ`.

- **Meeting context beats recipient type for meeting records**  
  - When the text clearly describes a meeting and associated elements (agenda, participants, decisions), the planner favors **documentation → meeting_minutes**, even if the recipient appears external or mixed.

- **Confirmation signals beat general communication signals**  
  - Strong confirmation triggers (e.g., `ვადასტურებთ`, `ეძლევა ცნობა`) promote **confirmation → certificate**, even if communication signals are also present.

- **Internal analytical requests default to memo**  
  - For internal channels and roles, with analytical or explanatory triggers (e.g., `მოგახსენებთ`, `აღსანიშნავია რომ`), the planner defaults to **analysis → memo** when no stronger decision, documentation, or confirmation signal exists.

These rules ensure that the strongest, most specific signals guide the final intent and format selection.

## Examples

### Example 1 – Meeting minutes

- **Request**: “გთხოვთ მოამზადოთ სხდომის ფარგლებში მიღებული გადაწყვეტილებების საფუძველზე შეხვედრის ოქმი.”  
- **Matched signals**:
  - Trigger: `სხდომის ფარგლებში` → documentation  
  - Action/document noun: “შეხვედრის ოქმი / meeting minutes” → documentation  
- **Resolved intent**: `documentation`  
- **Selected format**: `meeting_minutes`

### Example 2 – Administrative order

- **Request**: “დავალდეს სტრუქტურულ ერთეულებს უზრუნველყონ ახალი წესის შესრულება.”  
- **Matched signals**:
  - Trigger: `დავალდეს` → decision (very strong)  
  - Recipient context: internal units → internal decision  
- **Resolved intent**: `decision`  
- **Selected format**: `order`

### Example 3 – External official letter

- **Request**: “გიგზავნით ოფიციალურ წერილს პროექტის მიმდინარეობის შესახებ.”  
- **Matched signals**:
  - Trigger: `გიგზავნით` → communication  
  - Recipient type: external stakeholder  
- **Resolved intent**: `communication`  
- **Selected format**: `official_letter`

### Example 4 – Employment certificate

- **Request**: “ვადასტურებთ, რომ თანამშრომელი მუშაობს ჩვენს უწყებაში და ეძლევა ცნობა დასაქმების შესახებ.”  
- **Matched signals**:
  - Triggers: `ვადასტურებთ`, `ეძლევა ცნობა` → confirmation (very strong)  
- **Resolved intent**: `confirmation`  
- **Selected format**: `certificate`

### Example 5 – Internal analysis memo

- **Request**: “მოგახსენებთ, რომ არსებული პრაქტიკა საჭიროებს გადახედვას; გთხოვთ მოამზადოთ მოკლე ანალიტიკური ჩანაწერი.”  
- **Matched signals**:
  - Trigger: `მოგახსენებთ` → analysis  
  - Action: “მოკლე ანალიტიკური ჩანაწერი / analytic note” → analysis  
  - Recipient context: internal  
- **Resolved intent**: `analysis`  
- **Selected format**: `memo`

## Boundaries

- The **Router Agent** performs **workflow classification only** and does **not** use this signal model to select detailed document formats.  
- The **Document Planner** owns **signal interpretation, institutional intent detection, format selection, and section planning**.  
- The **Reply Agent** consumes the planner’s document plan to generate drafts and does **not** perform signal‑based format inference.  
- **GILE** remains **language refinement only**: it does **not** own intent or format logic and is responsible solely for institutional Georgian translation, rewrite, and validation.

