from typing import Any, Dict, List, Optional, Callable


OrchestratorRequest = Dict[str, Any]
OrchestratorResponse = Dict[str, Any]
RouterOutput = Dict[str, Any]
PlannerOutput = Dict[str, Any]
ReplyOutput = Dict[str, Any]


def run_orchestrator(
    request: OrchestratorRequest,
    router: Callable[[OrchestratorRequest], RouterOutput],
    planner: Callable[[Dict[str, Any]], PlannerOutput],
    reply_agent: Callable[[PlannerOutput], ReplyOutput],
    gile_client: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> OrchestratorResponse:
    """
    Entry point for the orchestrator runtime.

    The dependencies (router, planner, reply_agent, gile_client) are treated as
    opaque callables that respect the documented contracts in:
      - agents/HANDOFF_CONTRACTS.md
      - agents/schemas/
    """
    steps_executed: List[str] = []

    # Validate request
    steps_executed.append("validate_request")
    if not _validate_request(request):
        return _build_error_response(
            code="invalid_request",
            message="Request must contain 'message_text', 'metadata', and 'context'.",
            task_type=None,
            route=None,
            steps_executed=steps_executed,
            router_output=None,
            planner_output=None,
            reply_output=None,
        )

    # Call Router first
    try:
        router_output = router(request)
    except Exception as exc:  # pragma: no cover - dependency behavior
        return _build_error_response(
            code="invalid_router_output",
            message=f"Router call failed: {exc}",
            task_type=None,
            route=None,
            steps_executed=steps_executed,
            router_output=None,
            planner_output=None,
            reply_output=None,
        )

    steps_executed.append("router")

    steps_executed.append("validate_router_output")
    if not _validate_router_output(router_output):
        return _build_error_response(
            code="invalid_router_output",
            message="Router output does not match the expected contract.",
            task_type=router_output.get("task_type"),
            route=None,
            steps_executed=steps_executed,
            router_output=router_output,
            planner_output=None,
            reply_output=None,
        )

    task_type: str = router_output["task_type"]
    handoff_payload: Dict[str, Any] = router_output["handoff_payload"]

    planner_output: Optional[PlannerOutput] = None
    reply_output: Optional[ReplyOutput] = None
    gile_result: Optional[Dict[str, Any]] = None

    # Branch by task_type
    if task_type in {"translate", "rewrite", "validate"}:
        route_label = "direct_gile"
        try:
            gile_result = gile_client(handoff_payload)
            steps_executed.append("gile")
        except Exception as exc:  # pragma: no cover - dependency behavior
            return _build_error_response(
                code="gile_call_failed",
                message=f"GILE call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=None,
                reply_output=None,
            )

        final_output: Dict[str, Any] = gile_result if isinstance(gile_result, dict) else {
            "text": str(gile_result)
        }

        return {
            "status": "ok",
            "workflow": {
                "task_type": task_type,
                "route": route_label,
                "steps_executed": list(steps_executed),
            },
            "artifacts": {
                "router_output": router_output,
                "planner_output": None,
                "reply_output": None,
            },
            "final_output": final_output,
        }

    if task_type == "document_plan":
        route_label = "planner_only"

        try:
            planner_output = planner(handoff_payload)
            steps_executed.append("planner")
        except Exception as exc:  # pragma: no cover - dependency behavior
            return _build_error_response(
                code="invalid_planner_output",
                message=f"Planner call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=None,
                reply_output=None,
            )

        if not _validate_planner_output(planner_output):
            return _build_error_response(
                code="invalid_planner_output",
                message="Planner output does not match the expected contract.",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=None,
            )

        # For document_plan workflows, the planner's structured plan is the final output.
        final_output = planner_output

        return {
            "status": "ok",
            "workflow": {
                "task_type": task_type,
                "route": route_label,
                "steps_executed": list(steps_executed),
            },
            "artifacts": {
                "router_output": router_output,
                "planner_output": planner_output,
                "reply_output": None,
            },
            "final_output": final_output,
        }

    if task_type in {"document_draft", "reply_draft"}:
        # Planner
        route_label: str = "planner_reply_flow"

        try:
            planner_output = planner(handoff_payload)
            steps_executed.append("planner")
        except Exception as exc:  # pragma: no cover - dependency behavior
            return _build_error_response(
                code="invalid_planner_output",
                message=f"Planner call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=None,
                reply_output=None,
            )

        steps_executed.append("validate_planner_output")
        if not _validate_planner_output(planner_output):
            return _build_error_response(
                code="invalid_planner_output",
                message="Planner output does not match the expected contract.",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=None,
            )

        # Reply Agent
        try:
            reply_output = reply_agent(planner_output)
            steps_executed.append("reply")
        except Exception as exc:  # pragma: no cover - dependency behavior
            return _build_error_response(
                code="invalid_reply_output",
                message=f"Reply Agent call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=None,
            )

        steps_executed.append("validate_reply_output")
        if not _validate_reply_output(reply_output):
            return _build_error_response(
                code="invalid_reply_output",
                message="Reply output does not match the expected contract.",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=reply_output,
            )

        requires_gile = bool(reply_output.get("requires_gile"))

        if requires_gile:
            route_label = "planner_reply_gile"
            try:
                gile_result = gile_client(reply_output)
                steps_executed.append("gile")
            except Exception as exc:  # pragma: no cover - dependency behavior
                return _build_error_response(
                    code="gile_call_failed",
                    message=f"GILE call failed: {exc}",
                    task_type=task_type,
                    route=route_label,
                    steps_executed=steps_executed,
                    router_output=router_output,
                    planner_output=planner_output,
                    reply_output=reply_output,
                )

            final_output = gile_result if isinstance(gile_result, dict) else {
                "text": str(gile_result)
            }
        else:
            route_label = "planner_reply"
            # When GILE is not required, the reply draft artifact is the final output.
            final_output = reply_output

        return {
            "status": "ok",
            "workflow": {
                "task_type": task_type,
                "route": route_label,
                "steps_executed": list(steps_executed),
            },
            "artifacts": {
                "router_output": router_output,
                "planner_output": planner_output,
                "reply_output": reply_output,
            },
            "final_output": final_output,
        }

    if task_type == "needs_clarification":
        route_label = "clarification"
        # For clarification workflows, the router_output itself is treated as the clarification artifact.
        final_output = router_output

        return {
            "status": "clarification_required",
            "workflow": {
                "task_type": task_type,
                "route": route_label,
                "steps_executed": list(steps_executed),
            },
            "artifacts": {
                "router_output": router_output,
                "planner_output": None,
                "reply_output": None,
            },
            "final_output": final_output,
        }

    # Unsupported task_type
    return _build_error_response(
        code="unsupported_task_type",
        message=f"Unsupported task_type: {task_type}",
        task_type=task_type,
        route=None,
        steps_executed=steps_executed,
        router_output=router_output,
        planner_output=None,
        reply_output=None,
    )


def _validate_request(request: OrchestratorRequest) -> bool:
    """Validate the normalized orchestrator request shape."""
    if not isinstance(request, dict):
        return False

    required_fields = ["message_text", "metadata", "context"]
    for field in required_fields:
        if field not in request:
            return False

    if not isinstance(request["message_text"], str):
        return False
    if not isinstance(request["metadata"], dict):
        return False
    if not isinstance(request["context"], dict):
        return False

    return True


def _validate_router_output(router_output: RouterOutput) -> bool:
    """
    Validate Router output against the documented Router → Planner contract.
    """
    if not isinstance(router_output, dict):
        return False

    required_fields = [
        "task_type",
        "route_to",
        "confidence",
        "reasoning_summary",
        "handoff_payload",
    ]
    for field in required_fields:
        if field not in router_output:
            return False

    handoff_payload = router_output["handoff_payload"]
    if not isinstance(handoff_payload, dict):
        return False

    for field in ["message_text", "metadata", "context"]:
        if field not in handoff_payload:
            return False

    if not isinstance(handoff_payload["message_text"], str):
        return False
    if not isinstance(handoff_payload["metadata"], dict):
        return False
    if not isinstance(handoff_payload["context"], dict):
        return False

    return True


def _validate_planner_output(planner_output: PlannerOutput) -> bool:
    """
    Validate Planner output against the documented Planner → Reply Agent contract.
    """
    if not isinstance(planner_output, dict):
        return False

    required_fields = [
        "intent",
        "document_format",
        "confidence",
        "reasoning_summary",
        "sections",
        "draft_instructions",
        "source_payload",
    ]
    for field in required_fields:
        if field not in planner_output:
            return False

    sections = planner_output["sections"]
    if not isinstance(sections, list) or not sections:
        return False

    for section in sections:
        if not isinstance(section, dict):
            return False
        for field in ["id", "title", "purpose", "required"]:
            if field not in section:
                return False

    draft_instructions = planner_output["draft_instructions"]
    if not isinstance(draft_instructions, dict):
        return False
    for field in ["tone", "language"]:
        if field not in draft_instructions:
            return False

    if not isinstance(planner_output["source_payload"], dict):
        return False

    return True


def _validate_reply_output(reply_output: ReplyOutput) -> bool:
    """
    Validate Reply Agent output against the documented Reply Agent → GILE contract.
    """
    if not isinstance(reply_output, dict):
        return False

    required_fields = [
        "draft_text",
        "draft_language",
        "draft_type",
        "requires_gile",
        "gile_action",
        "source_plan",
    ]
    for field in required_fields:
        if field not in reply_output:
            return False

    if not isinstance(reply_output["draft_text"], str):
        return False
    if not isinstance(reply_output["draft_language"], str):
        return False
    if not isinstance(reply_output["draft_type"], str):
        return False
    if not isinstance(reply_output["requires_gile"], bool):
        return False
    if not isinstance(reply_output["gile_action"], str):
        return False
    if not isinstance(reply_output["source_plan"], dict):
        return False

    return True


def _build_error_response(
    code: str,
    message: str,
    task_type: Optional[str],
    route: Optional[str],
    steps_executed: List[str],
    router_output: Optional[RouterOutput],
    planner_output: Optional[PlannerOutput],
    reply_output: Optional[ReplyOutput],
) -> OrchestratorResponse:
    """
    Build a structured error response aligned with ORCHESTRATOR_INTERFACE.md.
    """
    return {
        "status": "error",
        "workflow": {
            "task_type": task_type,
            "route": route,
            "steps_executed": list(steps_executed),
        },
        "artifacts": {
            "router_output": router_output,
            "planner_output": planner_output,
            "reply_output": reply_output,
        },
        "final_output": None,
        "error": {
            "code": code,
            "message": message,
        },
    }

