from typing import Any, Dict, List, Optional, Callable


OrchestratorRequest = Dict[str, Any]
OrchestratorResponse = Dict[str, Any]
RouterOutput = Dict[str, Any]
PlannerOutput = Dict[str, Any]
ReplyOutput = Dict[str, Any]

# Frozen minimal contract surface v1: local string constants to reduce drift.
ROUTE_DIRECT_GILE = "direct_gile"
ROUTE_PLANNER_ONLY = "planner_only"
ROUTE_PLANNER_REPLY = "planner_reply"
ROUTE_PLANNER_REPLY_GILE = "planner_reply_gile"
ROUTE_PLANNER_REPLY_FLOW = "planner_reply_flow"
ROUTE_CLARIFICATION = "clarification"

ERROR_INVALID_REQUEST = "invalid_request"
ERROR_INVALID_ROUTER_OUTPUT = "invalid_router_output"
ERROR_INVALID_PLANNER_OUTPUT = "invalid_planner_output"
ERROR_INVALID_REPLY_OUTPUT = "invalid_reply_output"
ERROR_GILE_CALL_FAILED = "gile_call_failed"
ERROR_UNSUPPORTED_TASK_TYPE = "unsupported_task_type"

# Direct-GILE task family (router handoff goes straight to GILE).
DIRECT_GILE_TASK_TYPES = {
    "translate",
    "rewrite",
    "validate",
    "document_summarize",
}

# Planner/reply task family (router -> planner -> reply, optional GILE).
PLANNER_REPLY_TASK_TYPES = {
    "document_draft",
    "reply_draft",
    "email_draft",
}


def run_orchestrator(
    request: OrchestratorRequest,
    router: Callable[[OrchestratorRequest], RouterOutput],
    planner: Callable[[Dict[str, Any]], PlannerOutput],
    reply_agent: Callable[[PlannerOutput], ReplyOutput],
    gile_client: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> OrchestratorResponse:
    """
    Entry point for the orchestrator runtime.

    Coordinates the router, planner, reply agent, and GILE client to produce a
    structured OrchestratorResponse that includes workflow metadata and either
    a successful final_output or an error section. The orchestrator preserves
    existing route / error semantics and forwards GILE payloads without adding
    any extra schema normalization layer.
    """
    steps_executed: List[str] = []
    trace: List[str] = []

    # Validate request
    trace.append("validate_request")
    steps_executed.append("validate_request")
    if not _validate_request(request):
        trace.append("validation_failed_request")
        return _build_error_response(
            code=ERROR_INVALID_REQUEST,
            message="Request must contain 'message_text', 'metadata', and 'context'.",
            task_type=None,
            route=None,
            steps_executed=steps_executed,
            router_output=None,
            planner_output=None,
            reply_output=None,
            trace=trace,
        )

    # Call Router first
    try:
        trace.append("router_called")
        router_output = router(request)
    except Exception as exc:  # pragma: no cover - dependency behavior
        trace.append("router_call_failed")
        return _build_error_response(
            code=ERROR_INVALID_ROUTER_OUTPUT,
            message=f"Router call failed: {exc}",
            task_type=None,
            route=None,
            steps_executed=steps_executed,
            router_output=None,
            planner_output=None,
            reply_output=None,
            trace=trace,
        )

    steps_executed.append("router")

    steps_executed.append("validate_router_output")
    trace.append("validate_router_output")
    if not _validate_router_output(router_output):
        trace.append("validation_failed_router")
        return _build_error_response(
            code=ERROR_INVALID_ROUTER_OUTPUT,
            message="Router output does not match the expected contract.",
            task_type=router_output.get("task_type"),
            route=None,
            steps_executed=steps_executed,
            router_output=router_output,
            planner_output=None,
            reply_output=None,
            trace=trace,
        )

    task_type: str = router_output["task_type"]
    handoff_payload: Dict[str, Any] = router_output["handoff_payload"]

    planner_output: Optional[PlannerOutput] = None
    reply_output: Optional[ReplyOutput] = None
    gile_result: Optional[Dict[str, Any]] = None

    # Branch by task_type into the supported workflow categories.
    if task_type in DIRECT_GILE_TASK_TYPES:
        # Direct GILE flow: router handoff is validated, then sent straight to GILE.
        route_label = ROUTE_DIRECT_GILE
        try:
            # Validate router handoff before calling GILE.
            _validate_direct_gile_payload(handoff_payload)
            trace.append("direct_gile_path")
            trace.append("gile_called")
            gile_result = gile_client(handoff_payload)
            steps_executed.append("gile")
        except Exception as exc:  # pragma: no cover - dependency behavior
            trace.append("gile_call_failed")
            return _build_error_response(
                code=ERROR_GILE_CALL_FAILED,
                message=f"GILE call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=None,
                reply_output=None,
                trace=trace,
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
            "trace": list(trace),
        }

    if task_type == "document_plan":
        # Planner-only flow: planner produces a structured plan as final_output.
        route_label = ROUTE_PLANNER_ONLY

        try:
            trace.append("planner_called")
            planner_output = planner(handoff_payload)
            steps_executed.append("planner")
        except Exception as exc:  # pragma: no cover - dependency behavior
            trace.append("planner_call_failed")
            return _build_error_response(
                code=ERROR_INVALID_PLANNER_OUTPUT,
                message=f"Planner call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=None,
                reply_output=None,
                trace=trace,
            )

        try:
            _validate_planner_output(planner_output)
        except ValueError:
            trace.append("validation_failed_planner")
            return _build_error_response(
                code=ERROR_INVALID_PLANNER_OUTPUT,
                message="Planner output does not match the expected contract.",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=None,
                trace=trace,
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
            "trace": list(trace),
        }

    if task_type in PLANNER_REPLY_TASK_TYPES:
        # Planner -> reply flow, with optional GILE refinement based on requires_gile.
        route_label: str = ROUTE_PLANNER_REPLY_FLOW

        try:
            trace.append("planner_called")
            planner_output = planner(handoff_payload)
            steps_executed.append("planner")
        except Exception as exc:  # pragma: no cover - dependency behavior
            trace.append("planner_call_failed")
            return _build_error_response(
                code=ERROR_INVALID_PLANNER_OUTPUT,
                message=f"Planner call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=None,
                reply_output=None,
                trace=trace,
            )

        steps_executed.append("validate_planner_output")
        trace.append("validate_planner_output")
        try:
            _validate_planner_output(planner_output)
        except ValueError:
            trace.append("validation_failed_planner")
            return _build_error_response(
                code=ERROR_INVALID_PLANNER_OUTPUT,
                message="Planner output does not match the expected contract.",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=None,
                trace=trace,
            )

        # Reply Agent
        try:
            trace.append("reply_agent_called")
            reply_output = reply_agent(planner_output)
            steps_executed.append("reply")
        except Exception as exc:  # pragma: no cover - dependency behavior
            trace.append("reply_agent_call_failed")
            return _build_error_response(
                code=ERROR_INVALID_REPLY_OUTPUT,
                message=f"Reply Agent call failed: {exc}",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=None,
                trace=trace,
            )

        steps_executed.append("validate_reply_output")
        trace.append("validate_reply_output")
        if not _validate_reply_output(reply_output):
            trace.append("validation_failed_reply")
            return _build_error_response(
                code=ERROR_INVALID_REPLY_OUTPUT,
                message="Reply output does not match the expected contract.",
                task_type=task_type,
                route=route_label,
                steps_executed=steps_executed,
                router_output=router_output,
                planner_output=planner_output,
                reply_output=reply_output,
                trace=trace,
            )

        requires_gile = bool(reply_output.get("requires_gile"))

        if requires_gile:
            route_label = ROUTE_PLANNER_REPLY_GILE
            try:
                # Validate reply output before calling GILE.
                _validate_reply_gile_payload(reply_output)
                trace.append("planner_reply_gile_path")
                trace.append("gile_called")
                gile_result = gile_client(reply_output)
                steps_executed.append("gile")
            except Exception as exc:  # pragma: no cover - dependency behavior
                trace.append("gile_call_failed")
                return _build_error_response(
                    code=ERROR_GILE_CALL_FAILED,
                    message=f"GILE call failed: {exc}",
                    task_type=task_type,
                    route=route_label,
                    steps_executed=steps_executed,
                    router_output=router_output,
                    planner_output=planner_output,
                    reply_output=reply_output,
                    trace=trace,
                )

            final_output = gile_result if isinstance(gile_result, dict) else {
                "text": str(gile_result)
            }
        else:
            route_label = ROUTE_PLANNER_REPLY
            # Planner -> reply flow without GILE: reply draft becomes final_output.
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
            "trace": list(trace),
        }

    if task_type == "needs_clarification":
        route_label = ROUTE_CLARIFICATION
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
            "trace": list(trace),
        }

    # Unsupported task_type: surface a structured error without attempting further calls.
    return _build_error_response(
        code=ERROR_UNSUPPORTED_TASK_TYPE,
        message=f"Unsupported task_type: {task_type}",
        task_type=task_type,
        route=None,
        steps_executed=steps_executed,
        router_output=router_output,
        planner_output=None,
        reply_output=None,
        trace=trace,
    )


def _validate_direct_gile_payload(payload: Dict[str, Any]) -> None:
    """
    Used before direct calls to GILE (translate, rewrite, validate).
    Required fields: "message_text", "metadata", "context".
    Payload is expected from router_output["handoff_payload"].
    Raises ValueError if invalid.
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid GILE handoff payload (direct flow)")
    for key in ("message_text", "metadata", "context"):
        if key not in payload:
            raise ValueError("Invalid GILE handoff payload (direct flow)")


def _validate_reply_gile_payload(payload: Dict[str, Any]) -> None:
    """
    Used before reply-driven calls to GILE when requires_gile is True.
    Required fields: "draft_text", "draft_language", "draft_type", "gile_action".
    Payload is expected from reply_output.
    Raises ValueError if invalid.
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid GILE handoff payload (reply flow)")
    for key in ("draft_text", "draft_language", "draft_type", "gile_action"):
        if key not in payload:
            raise ValueError("Invalid GILE handoff payload (reply flow)")


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


def _validate_planner_output(planner_output: dict) -> None:
    """
    Validate only the frozen minimal planner contract fragment before reply-stage use.

    Frozen top-level required fields:
    - intent
    - sections
    - draft_instructions

    Frozen required fields inside sections[]:
    - id
    - title
    - purpose
    - required

    Frozen required fields inside draft_instructions:
    - language
    - tone
    - constraints

    This is intentionally not a closed full-schema validation. Extra planner fields
    remain allowed and are not rejected here.
    """
    if not isinstance(planner_output, dict):
        raise ValueError("Invalid planner output")

    for field in ("intent", "sections", "draft_instructions"):
        if field not in planner_output:
            raise ValueError("Invalid planner output")

    intent = planner_output["intent"]
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("Invalid planner output")

    sections = planner_output["sections"]
    if not isinstance(sections, list):
        raise ValueError("Invalid planner output")

    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("Invalid planner output")

        for field in ("id", "title", "purpose", "required"):
            if field not in section:
                raise ValueError("Invalid planner output")

        if not isinstance(section["id"], str) or not section["id"].strip():
            raise ValueError("Invalid planner output")
        if not isinstance(section["title"], str) or not section["title"].strip():
            raise ValueError("Invalid planner output")
        if not isinstance(section["purpose"], str) or not section["purpose"].strip():
            raise ValueError("Invalid planner output")
        if not isinstance(section["required"], bool):
            raise ValueError("Invalid planner output")

    draft_instructions = planner_output["draft_instructions"]
    if not isinstance(draft_instructions, dict):
        raise ValueError("Invalid planner output")

    for field in ("language", "tone", "constraints"):
        if field not in draft_instructions:
            raise ValueError("Invalid planner output")

    if (
        not isinstance(draft_instructions["language"], str)
        or not draft_instructions["language"].strip()
    ):
        raise ValueError("Invalid planner output")

    if (
        not isinstance(draft_instructions["tone"], str)
        or not draft_instructions["tone"].strip()
    ):
        raise ValueError("Invalid planner output")

    if not isinstance(draft_instructions["constraints"], list):
        raise ValueError("Invalid planner output")


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
    trace: List[str],
) -> OrchestratorResponse:
    """
    Build a structured error response aligned with ORCHESTRATOR_INTERFACE.md.

    workflow.route communicates the resolved execution path (when known), and
    error.code communicates the failure classification used by callers.
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
        "trace": list(trace),
    }

