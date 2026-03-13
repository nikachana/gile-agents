## Architecture

This repository is part of a **two‑repository architecture**:

- **`gile`** – institutional Georgian language engine (external).
- **`gile-agents`** – reasoning agents that orchestrate workflows and call GILE.

There is a strict separation of concerns:

- **GILE = language layer**
- **Agents = reasoning layer**

## Two‑Repository Responsibilities

Agents should treat GILE as a stateless language engine.
All reasoning, task interpretation, and workflow decisions remain in the agent layer.

### GILE (language layer, separate repo)

**Responsible for:**
- English → Georgian institutional translation.
- Georgian → Georgian institutional rewrite and refinement.
- Enforcing institutional terminology and style.
- Retrieval and example provision for language use.
- Editor‑style passes and validation of language output.

**Must never contain:**
- Business‑specific routing or workflow orchestration.
- Agent‑style multi‑step reasoning or task decomposition.
- Cross‑agent planning logic.

### gile-agents (reasoning layer, this repo)

**Responsible for:**
- Interpreting incoming messages and selecting workflows (routing).
- Planning documents, responses, and interaction structures.
- Producing **draft intent/content** in English or Georgian.
- Orchestrating calls to GILE and other external systems.

**Must never do:**
- Final institutional Georgian refinement without GILE.
- Re‑implementing GILE translation, rewrite, or validation logic.
- Bypassing GILE when producing official Georgian output.

Integration principle: **every final institutional Georgian output must pass through GILE** before being returned.

## Document Format Knowledge

Institutional document types such as **official letters, meeting minutes, protocols, decrees, certificates, and memos** are treated as **structural formats** in this architecture.
These formats define **layout and section structure** and are handled by the **Document Planner** in `gile-agents`.

- **Document Planner (agents layer)**: chooses and applies the appropriate institutional format, defines sections, and describes the intent of each part.
- **GILE (language layer)**: operates on the text produced according to that structure, providing translation, rewrite, refinement, terminology enforcement, retrieval, and validation.

GILE is **not** responsible for choosing document formats or designing document structure; it only refines and validates the language that follows the structure defined by the agents.

## Target Flow

The target high‑level flow for a message is:

Incoming message  
→ **Router Agent** (selects workflow / task type)  
→ **Reasoning / Planning Agent** (e.g., Document Planner)  
→ **Draft response (EN or KA)** produced by agents  
→ **GILE** (translation / rewrite / refinement / validation / terminology / retrieval / editor pass)  
→ **Institutional Georgian output** returned to the user or system

In this flow:
- Agents may reason internally in English.
- Drafts may be in English or preliminary Georgian.
- **Only GILE** is trusted to produce or finalize institutional Georgian text.

