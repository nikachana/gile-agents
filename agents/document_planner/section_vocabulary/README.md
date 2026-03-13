## Georgian Institutional Section Vocabulary (v1)

The Georgian Institutional Section Vocabulary defines a **shared set of section identifiers** that can be reused across institutional document formats. It is owned by the **Document Planner** and is intended to keep section naming consistent and predictable.

- **Purpose**: provide a stable vocabulary of sections (e.g., `header`, `subject_line`, `decision_points`) that formats and planners can reference.
- **Relationship with document formats**: document formats (such as `official_letter`, `order`, `meeting_minutes`, `certificate`, `memo`) select and arrange sections from this vocabulary to build their structures.
- **Reuse across formats**: the same section (for example, `header` or `signature_block`) may appear in multiple formats, with the **same semantic meaning**, even if the detailed wording differs by context.

### Usage by Planners and Reply Agents

- **Document Planner**:
  - Uses the section vocabulary to define `sections` in plans.
  - Ensures that `section_id` values in plans align with this shared vocabulary.
  - Chooses which sections are required or optional for each format.
- **Reply Agent**:
  - Consumes plans that reference these `section_id` values.
  - Drafts content for each section based on its **purpose/description**, not by redefining the section semantics.

Neither the section vocabulary nor the format definitions contain **full prose templates**. They describe **structure and intent only**; **GILE** remains responsible for language‑level translation, rewrite, refinement, and validation.

