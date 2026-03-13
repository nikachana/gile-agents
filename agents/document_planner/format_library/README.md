## Georgian Institutional Document Format Library (v1)

This library defines **Georgian institutional document formats** for use by the **Document Planner**. It provides structural definitions (sections, ordering, required elements, and planning hints) that the planner can use when generating plans for institutional documents.

- The **Document Planner** owns document **format selection and application**.
- The **Router Agent** may pass hints but **does not own** format logic or structure.
- The **Reply Agent** must **not invent institutional formats**; it drafts against the structure defined by the planner and this library.
- **GILE** remains **pure language infrastructure** and **must not own or encode document formats**; it operates only on drafted text and performs translation, rewrite, refinement, terminology enforcement, retrieval, and validation.

Each format file in this directory:

- Defines **structure**, **section order**, and **required vs. optional elements**.
- Provides **planning hints** to guide how sections should be used.
- Does **not** contain full prose templates or final wording.

These formats are **planning artifacts only**. They are consumed by the Document Planner to build plans that are later drafted by the Reply Agent and refined by GILE.

