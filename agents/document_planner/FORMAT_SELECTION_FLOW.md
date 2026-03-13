# Format Selection Flow

## Purpose

This document defines the **standard planning pipeline** used by the **Document Planner** to select a Georgian institutional document format and structure **before any drafting begins**.

## Flow Overview

The canonical format selection flow is:

Incoming request  
↓  
Intent detection  
↓  
Intent → format mapping  
↓  
Load format structure  
↓  
Load section vocabulary  
↓  
Return document plan

## Step‑by‑Step Explanation

### Incoming request

- Input arrives from the **Router Agent** after first‑pass workflow classification.  
- The request includes:
  - **task type** (e.g., `reply_draft`, `document_draft`, `document_plan`),
  - **message text** (user or system request),
  - **context** (metadata, conversation history, related documents, constraints).

### Intent detection

- The planner identifies the **institutional purpose** of the request (e.g., communication, decision, documentation, confirmation, analysis).  
- Detection relies on:
  - the **intent taxonomy** (`intent_taxonomy.json`),
  - task type, trigger words, recipient type, and context.

### Intent → format mapping

- The detected **intent** is mapped to one of the approved **v1 formats**.  
- Mapping follows the canonical taxonomy:
  - **communication** → `official_letter`
  - **decision** → `order`
  - **documentation** → `meeting_minutes`
  - **confirmation** → `certificate`
  - **analysis** → `memo`

### Load format structure

- The planner retrieves the selected format definition from the **format library** (`format_library/`).  
- It loads the format’s:
  - `required_sections`,
  - `optional_sections`.

### Load section vocabulary

- For each section ID, the planner consults the **section vocabulary** (`section_vocabulary/sections.json`).  
- This ensures that section meanings (e.g., `header`, `meeting_details`, `decision_points`) are:
  - consistent across formats,
  - described with clear institutional semantics.

### Return document plan

- The planner returns a **document plan** to the Reply Agent, including:
  - selected **intent** and **document_format**,
  - ordered list of **sections** (required + chosen optional),
  - high‑level **drafting instructions** (tone, length, style hints).
- This plan is a **structural contract**; it does **not** contain final text or Georgian refinement.

## Approved v1 Intents and Formats

The v1 system uses the following approved intent → format mapping:

- **communication** → `official_letter`
- **decision** → `order`
- **documentation** → `meeting_minutes`
- **confirmation** → `certificate`
- **analysis** → `memo`

## Boundaries

- The **Router Agent** performs **workflow classification only** and **does not select** detailed document formats.  
- The **Document Planner** detects intent, selects format, and plans sections, but **does not write final text**.  
- The **Reply Agent** creates drafts based on the planner’s structure and **does not invent new document structures or formats**.  
- **GILE** remains **pure language infrastructure**: it **does not own format logic** and is responsible only for **Georgian institutional language refinement** (translation, rewrite, terminology enforcement, validation).

## Example

**Request**: “Please prepare minutes of today’s project coordination meeting.”  

- **Detected intent**: `documentation`  
- **Selected format**: `meeting_minutes`  
- **Resulting sections** (conceptual example):
  - `meeting_details`
  - `participants`
  - `agenda`
  - `discussion_summary`
  - `decisions`
  - `action_items`

The Document Planner returns a plan with these sections and relevant drafting instructions. The Reply Agent then drafts content for each section, and GILE later refines the draft into institutional Georgian.

