def planner(router_output: dict) -> dict:
    """
    Deterministic v1 planner skeleton.

    This planner does not call any model.
    It converts Router output (or the Router handoff_payload passed by the
    orchestrator) into a contract-shaped planner_output artifact that matches
    the approved planner schema.
    """

    # In the orchestrator, the planner is invoked with router_output["handoff_payload"].
    # Here we support both full router_output and a bare handoff_payload dict.
    if "handoff_payload" in router_output:
        payload = router_output.get("handoff_payload") or {}
        task_type = router_output.get("task_type", "")
    else:
        payload = router_output or {}
        # When only the payload is available, infer the workflow type from metadata.mode.
        mode = (payload.get("metadata") or {}).get("mode")
        if mode == "document_plan":
            task_type = "document_plan"
        elif mode == "reply_draft":
            task_type = "reply_draft"
        else:
            task_type = "document_draft"

    message_text = payload.get("message_text", "") or ""
    metadata = payload.get("metadata", {}) or {}
    context = payload.get("context", {}) or {}

    # Shared, contract-aligned fields
    intent = "documentation" if task_type == "document_plan" else "communication"
    document_format = metadata.get("document_format") or "official_letter"
    format_variant = metadata.get("format_variant") or "stub_default"
    confidence = 1.0

    reasoning_summary = (
        "Deterministic planner_stub: produced a simple plan for document_plan."
        if task_type == "document_plan"
        else "Deterministic planner_stub: produced a simple plan for drafting workflow."
    )

    sections = [
        {
            "id": "opening",
            "title": "Opening",
            "purpose": "Introduce the document and its purpose.",
            "required": True,
        },
        {
            "id": "main_points",
            "title": "Main Points",
            "purpose": "Present the main points or decisions.",
            "required": True,
        },
        {
            "id": "closing",
            "title": "Closing",
            "purpose": "Provide closing remarks and any follow-up actions.",
            "required": True,
        },
    ]

    draft_instructions = {
        "tone": metadata.get("tone", "formal_institutional"),
        "language": metadata.get("language", "en"),
        "constraints": [],
    }

    source_payload = {
        "router_task_type": task_type,
        "original_message_text": message_text,
        "metadata": metadata,
        "context": context,
    }

    return {
        "intent": intent,
        "document_format": document_format,
        "format_variant": format_variant,
        "confidence": confidence,
        "reasoning_summary": reasoning_summary,
        "risk_flags": [],
        "sections": sections,
        "draft_instructions": draft_instructions,
        "source_payload": source_payload,
    }

