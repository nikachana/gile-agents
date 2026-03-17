def reply_agent(planner_output: dict) -> dict:
    """
    Deterministic v1 Reply Agent skeleton.

    This reply agent does not call any model.
    It converts a contract-shaped planner_output into a contract-shaped
    reply_output suitable for optional GILE refinement.
    """
    # Determine basic properties from the planner output
    document_format = planner_output.get("document_format") or "official_letter"
    draft_language = (planner_output.get("draft_instructions") or {}).get("language") or "en"
    sections = planner_output.get("sections") or []
    source_payload = planner_output.get("source_payload") or {}

    router_task_type = source_payload.get("router_task_type", "")
    original_message_text = source_payload.get("original_message_text", "")

    # Decide whether GILE is required based on the originating workflow
    requires_gile = router_task_type == "document_draft"

    if requires_gile:
        gile_action = "institutional_rewrite"
    else:
        gile_action = "rewrite"

    # Build a simple, deterministic draft text from the plan
    section_titles = [section.get("title", "") for section in sections if section.get("title")]
    section_part = " | ".join(section_titles) if section_titles else "Draft"

    if original_message_text:
        draft_text = f"[{document_format}] {section_part}: {original_message_text}"
    else:
        draft_text = f"[{document_format}] {section_part}: Draft generated from planner output."

    style_hints = [
        f"Use tone '{(planner_output.get('draft_instructions') or {}).get('tone', 'formal_institutional')}'."
    ]

    return {
        "draft_text": draft_text,
        "draft_language": draft_language,
        "draft_type": document_format,
        "requires_gile": requires_gile,
        "gile_action": gile_action,
        "style_hints": style_hints,
        "redaction_notes": [],
        "segment_map": [],
        "source_plan": dict(planner_output),
    }

