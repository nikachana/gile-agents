def router(request: dict) -> dict:
    """
    Deterministic v1 router skeleton.

    This router does not perform any model calls.
    It only maps request content to a contract-shaped router output.
    """

    message_text = request.get("message_text", "")
    metadata = request.get("metadata", {}) or {}
    context = request.get("context", {}) or {}

    normalized_message = message_text.strip() if isinstance(message_text, str) else ""
    mode = metadata.get("mode")

    if not normalized_message:
        task_type = "needs_clarification"
    elif mode == "translate":
        task_type = "translate"
    elif mode == "rewrite":
        task_type = "rewrite"
    elif mode == "validate":
        task_type = "validate"
    elif mode == "document_plan":
        task_type = "document_plan"
    elif mode == "reply_draft":
        task_type = "reply_draft"
    else:
        task_type = "document_draft"

    route_to = _route_for_task_type(task_type)

    return {
        "task_type": task_type,
        "route_to": route_to,
        "confidence": 1.0,
        "reasoning_summary": "Deterministic router_stub: task_type selected from metadata.mode and message presence.",
        "handoff_payload": {
            "message_text": normalized_message,
            "metadata": metadata,
            "context": context,
        },
    }


def _route_for_task_type(task_type: str) -> str:
    if task_type in {"translate", "rewrite", "validate"}:
        return "gile"
    if task_type == "document_plan":
        return "planner"
    if task_type in {"document_draft", "reply_draft"}:
        return "planner"
    if task_type == "needs_clarification":
        return "clarification"
    return "unsupported"

