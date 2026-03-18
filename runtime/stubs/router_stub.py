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

    # Explicit mode -> task_type mapping for supported task families.
    _MODE_TO_TASK_TYPE = {
        "translate": "translate",
        "rewrite": "rewrite",
        "validate": "validate",
        "document_plan": "document_plan",
        "reply_draft": "reply_draft",
        "document_summarize": "document_summarize",
        "email_draft": "email_draft",
    }

    if not normalized_message:
        task_type = "needs_clarification"
    else:
        task_type = _MODE_TO_TASK_TYPE.get(mode, "document_draft")

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
    _TASK_TO_ROUTE = {
        "translate": "gile",
        "rewrite": "gile",
        "validate": "gile",
        "document_summarize": "gile",
        "document_plan": "planner",
        "document_draft": "planner",
        "reply_draft": "planner",
        "email_draft": "planner",
        "needs_clarification": "clarification",
    }

    return _TASK_TO_ROUTE.get(task_type, "unsupported")

