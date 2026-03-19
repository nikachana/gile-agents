from typing import Any, Dict

from runtime.orchestration.orchestrator import run_orchestrator


def _valid_request(mode: str = "document_draft") -> Dict[str, Any]:
    return {
        "message_text": "Test message",
        "metadata": {"mode": mode},
        "context": {},
    }


def _valid_router_output(task_type: str = "document_draft") -> Dict[str, Any]:
    return {
        "task_type": task_type,
        "route_to": "planner",
        "confidence": 1.0,
        "reasoning_summary": "test router",
        "handoff_payload": {
            "message_text": "handoff",
            "metadata": {},
            "context": {},
        },
    }


def _valid_planner_output(_payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": "communication",
        "sections": [{"id": "s1", "title": "Body", "purpose": "Main", "required": True}],
        "draft_instructions": {"language": "en", "tone": "formal", "constraints": []},
    }


def _valid_reply_output(_plan: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "requires_gile": False,
        "draft_text": "draft",
        "draft_language": "en",
        "draft_type": "generic",
        "gile_action": "none",
    }


def test_invalid_request_has_validation_trace_and_single_step():
    result = run_orchestrator(
        request={"message_text": "x", "metadata": {}},
        router=lambda req: _valid_router_output(),
        planner=_valid_planner_output,
        reply_agent=_valid_reply_output,
        gile_client=lambda payload: {"text": "ok"},
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_request"
    assert result["workflow"]["steps_executed"] == ["validate_request"]
    assert result["trace"] == ["validate_request", "validation_failed_request"]


def test_router_call_failure_has_consistent_trace_and_steps():
    def failing_router(_request):
        raise RuntimeError("router boom")

    result = run_orchestrator(
        request=_valid_request(),
        router=failing_router,
        planner=_valid_planner_output,
        reply_agent=_valid_reply_output,
        gile_client=lambda payload: {"text": "ok"},
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_router_output"
    assert result["workflow"]["steps_executed"] == ["validate_request"]
    assert result["trace"] == ["validate_request", "router_called", "router_call_failed"]


def test_planner_call_failure_has_consistent_trace_and_steps():
    def failing_planner(_payload):
        raise RuntimeError("planner boom")

    result = run_orchestrator(
        request=_valid_request("document_draft"),
        router=lambda req: _valid_router_output("document_draft"),
        planner=failing_planner,
        reply_agent=_valid_reply_output,
        gile_client=lambda payload: {"text": "ok"},
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_planner_output"
    assert result["workflow"]["steps_executed"] == [
        "validate_request",
        "router",
        "validate_router_output",
    ]
    assert result["trace"] == [
        "validate_request",
        "router_called",
        "validate_router_output",
        "planner_called",
        "planner_call_failed",
    ]


def test_reply_agent_call_failure_has_consistent_trace_and_steps():
    def failing_reply(_plan):
        raise RuntimeError("reply boom")

    result = run_orchestrator(
        request=_valid_request("document_draft"),
        router=lambda req: _valid_router_output("document_draft"),
        planner=_valid_planner_output,
        reply_agent=failing_reply,
        gile_client=lambda payload: {"text": "ok"},
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_reply_output"
    assert result["workflow"]["steps_executed"] == [
        "validate_request",
        "router",
        "validate_router_output",
        "planner",
        "validate_planner_output",
    ]
    assert result["trace"] == [
        "validate_request",
        "router_called",
        "validate_router_output",
        "planner_called",
        "validate_planner_output",
        "reply_agent_called",
        "reply_agent_call_failed",
    ]


def test_direct_gile_call_failure_has_consistent_trace_and_steps():
    def failing_gile(_payload):
        raise RuntimeError("gile boom")

    result = run_orchestrator(
        request=_valid_request("translate"),
        router=lambda req: _valid_router_output("translate"),
        planner=_valid_planner_output,
        reply_agent=_valid_reply_output,
        gile_client=failing_gile,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "gile_call_failed"
    assert result["workflow"]["steps_executed"] == [
        "validate_request",
        "router",
        "validate_router_output",
        "validate_direct_gile_payload",
    ]
    assert result["trace"] == [
        "validate_request",
        "router_called",
        "validate_router_output",
        "validate_direct_gile_payload",
        "direct_gile_path",
        "gile_called",
        "gile_call_failed",
    ]


def test_planner_reply_gile_call_failure_has_consistent_trace_and_steps():
    def requires_gile_reply(_plan):
        return {
            "requires_gile": True,
            "draft_text": "draft",
            "draft_language": "en",
            "draft_type": "generic",
            "gile_action": "rewrite",
        }

    def failing_gile(_payload):
        raise RuntimeError("gile boom")

    result = run_orchestrator(
        request=_valid_request("document_draft"),
        router=lambda req: _valid_router_output("document_draft"),
        planner=_valid_planner_output,
        reply_agent=requires_gile_reply,
        gile_client=failing_gile,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "gile_call_failed"
    assert result["workflow"]["steps_executed"] == [
        "validate_request",
        "router",
        "validate_router_output",
        "planner",
        "validate_planner_output",
        "reply",
        "validate_reply_output",
    ]
    assert result["trace"] == [
        "validate_request",
        "router_called",
        "validate_router_output",
        "planner_called",
        "validate_planner_output",
        "reply_agent_called",
        "validate_reply_output",
        "planner_reply_gile_path",
        "gile_called",
        "gile_call_failed",
    ]


def test_unsupported_task_type_has_consistent_trace_and_steps():
    result = run_orchestrator(
        request=_valid_request(),
        router=lambda req: _valid_router_output("unknown_task"),
        planner=_valid_planner_output,
        reply_agent=_valid_reply_output,
        gile_client=lambda payload: {"text": "ok"},
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "unsupported_task_type"
    assert result["workflow"]["steps_executed"] == [
        "validate_request",
        "router",
        "validate_router_output",
    ]
    assert result["trace"] == [
        "validate_request",
        "router_called",
        "validate_router_output",
    ]
